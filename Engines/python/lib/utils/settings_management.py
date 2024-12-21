import os
import sys
import shutil
import logging
import configparser
import commentedconfigparser

from .file_management import file_critical_check
from .pausing import pause
from .FILE_INFO import (
    SETTINGS_PATH,
    SETTINGS_DEFAULT_PATH,
)


def settings_transfer(file_old_path, file_new_path, transfer_table_path = None):

    config_old = commentedconfigparser.CommentedConfigParser()
    config_old.read(file_old_path)
    config_new = commentedconfigparser.CommentedConfigParser()
    config_new.read(file_new_path)

    # Prepare lists to store any new or missing settings
    settings_added = []
    settings_removed = []
    settings_renamed = []

    if transfer_table_path is not None:

        # Prepare a dictionary of settings that need to be renamed
        settings_transfer_dict = {}

        with open(transfer_table_path, 'r', encoding='utf-8') as f:
            transfer_table = f.readlines()
        transfer_table = [line.strip() for line in transfer_table]

        # Parse the transfer table
        # The format is "setting_old -> setting_new"
        for line in transfer_table:
            setting_old, setting_new = line.split(" -> ")
            settings_transfer_dict[setting_old] = setting_new

        # Rename all the settings in the old config
        for section in config_old.sections():
            for key, value in config_old.items(section):
                if key in settings_transfer_dict:
                    key_new = settings_transfer_dict[key]

                    # Check if the new name exists in the new config
                    for section_new in config_new.sections():
                        if key_new in config_new[section_new]:
                            settings_renamed.append((section, section_new))
                            # Delete the old setting
                            config_old.remove_option(section, key)
                            # Recreate the setting with the new name
                            config_old.set(section, key_new, value)
                            break

    # Iterate over all the settings in the new config
    for section_new in config_new.sections():
        for key_new, value_new in config_new.items(section_new):

            # Check if the setting exists in the old config
            for section_old in config_old.sections():
                if key_new in config_old[section_old]:
                    break
            else:
                settings_added.append(section_new)

    # Iterate over all the settings in the old config
    for section_old in config_old.sections():
        for key_old, value_old in config_old.items(section_old):

            # Check if the setting exists in the new config
            for section_new in config_new.sections():
                if key_old in config_new[section_new]:
                    config_new[section_new][key_old] = value_old
                    break
            else:
                settings_removed.append(section_old)

    # Write the new config to the file
    with open(file_new_path, 'w', encoding="utf8") as configfile:
        config_new.write(configfile)

    # Add a blank line after lines 1 and 4 to the new config file
    # to preserve the original formatting
    with open(file_new_path, 'r', encoding="utf8") as f:
        lines = f.readlines()
        lines.insert(1, '\n')
        lines.insert(4, '\n')
    with open(file_new_path, 'w', encoding="utf8") as f:
        f.writelines(lines)

    return settings_added, settings_removed, settings_renamed


def settings_missing_check(default_file_path):

    # Prepare a list with the required settings
    required_settings = [
        'PES_VERSION',
        'CPK_NAME',
        'PES_FOLDER_PATH',
    ]

    # Check if all the required settings have been loaded
    settings_missing = [setting for setting in required_settings if setting not in os.environ]

    # If any required settings are missing, there is no need to continue
    if settings_missing:
        return settings_missing

    # Read the default settings file
    config = configparser.ConfigParser()
    config.read(default_file_path)

    # Check if any settings are missing and load them into the environment
    # with the values from the default settings file
    for section in config.sections():
        for key, value in config.items(section):
            setting_name = key.upper()
            if setting_name not in os.environ:
                os.environ[setting_name] = value

    return False


def settings_default_init(file_path, default_file_path):

    # If there already is a main settings file, rename it by appending "_old" to it
    if os.path.isfile(file_path):

        # Grab the extension of the file
        file_extension = os.path.splitext(file_path)[1]

        # Prepare the name of the old settings file, with "_old" appended
        old_file_name = os.path.basename(file_path).replace(file_extension, "_old" + file_extension)

        # Check if an old settings file already exists and delete it
        if os.path.isfile(old_file_name):
            os.remove(old_file_name)

        # Rename the main settings file
        os.rename(file_path, old_file_name)

        if sys.platform == "win32":
            # Open it in an external text editor
            os.startfile(old_file_name)

    # Copy the default settings file to the main folder, with the original name
    shutil.copy(default_file_path, file_path)

    if sys.platform == "win32":
        # Open the settings file in an external text editor
        os.startfile(file_path)

    # Exit the script
    exit()


def settings_init():

    # Check if the default settings file exists
    file_critical_check(SETTINGS_DEFAULT_PATH)

    SETTINGS_NAME = os.path.basename(SETTINGS_PATH)

    # Check if the file exists
    if not os.path.isfile(SETTINGS_PATH):

        logging.critical( "-")
        logging.critical(f"- FATAL ERROR - Missing \"{SETTINGS_NAME}\" file")
        logging.critical( "-")
        logging.critical( "- A clean settings file will be generated and opened")
        logging.critical( "- Please edit the settings as needed and restart the program")
        print("-")
        pause("Press any key to continue... ")

        settings_default_init(SETTINGS_PATH, SETTINGS_DEFAULT_PATH)

    else:

        # Read the settings
        config = configparser.ConfigParser()
        config.read(SETTINGS_PATH)

        for section in config.sections():
            for key, value in config.items(section):
                os.environ[key.upper()] = value

        # Check if any required settings are missing
        settings_missing = settings_missing_check(SETTINGS_DEFAULT_PATH)
        if settings_missing:

            logging.critical( "-")
            logging.critical( "- FATAL ERROR - Missing settings")
            logging.critical(f"- The following required settings are missing from the \"{SETTINGS_NAME}\" file:")
            # Log the list of missing required settings
            for setting in settings_missing:
                logging.critical(f"- \"{setting.lower()}\"")
            logging.critical( "-")
            logging.critical( "- Please edit the settings file as needed and restart the program")
            print( "-")
            print( "-")
            print( "- If you type \"new\" and press Enter,")
            print( "- a clean settings file will be generated and opened, and")
            print( "- the old file will be renamed with \"_old\" at the end and opened too")
            print("-")
            choice = input("Type \"new\" and press Enter, or just press Enter to exit...")

            if "new" in choice:
                settings_default_init(SETTINGS_PATH, SETTINGS_DEFAULT_PATH)
            else:
                exit()

        # Check if the PES download folder location contains the magic number ** and replace it with the pes version
        pes_folder_path = os.environ.get("PES_FOLDER_PATH", 'unknown')
        if "**" in pes_folder_path:
            os.environ["PES_FOLDER_PATH"] = pes_folder_path.replace("**", os.environ["PES_VERSION"])

        # Prepare the path to the PES exe in the parent folder of the PES download folder
        pes_exe_name = "PES20" + os.environ["PES_VERSION"] + ".exe"
        os.environ["PES_EXE_PATH"] = os.path.join(os.environ["PES_FOLDER_PATH"], pes_exe_name)
