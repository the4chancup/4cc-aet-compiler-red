import os
import sys
import shutil
import logging
import configparser

from .file_management import file_critical_check
from .pausing import pause


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


def settings_default_path_get(file_path):

    # Grab the extension of the file
    file_extension = os.path.splitext(file_path)[1]

    # Prepare the name of the default settings file, with "_default" appended
    default_file_name = os.path.basename(file_path).replace(file_extension, "_default" + file_extension)

    # Prepare the path to the default settings file inside the Engines\templates folder
    default_file_path = os.path.join(os.path.dirname(file_path), "Engines", "templates", default_file_name)

    # Check if the default settings file exists
    file_critical_check(default_file_path)

    return default_file_path


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


def settings_init(file_name):

    # Prepare the name of the default settings file
    default_file_path = settings_default_path_get(file_name)

    # Check if the file exists
    if not os.path.isfile(file_name):

        logging.critical( "-")
        logging.critical(f"- FATAL ERROR - Missing \"{file_name}\" file")
        logging.critical( "-")
        logging.critical( "- A clean settings file will be generated and opened")
        logging.critical( "- Please edit the settings as needed and restart the program")
        print("-")
        pause("Press any key to continue... ")

        settings_default_init(file_name, default_file_path)

    else:

        # Read the settings
        config = configparser.ConfigParser()
        config.read(file_name)

        for section in config.sections():
            for key, value in config.items(section):
                os.environ[key.upper()] = value

        # Check if any required settings are missing
        settings_missing = settings_missing_check(default_file_path)
        if settings_missing:

            logging.critical( "-")
            logging.critical( "- FATAL ERROR - Missing settings")
            logging.critical(f"- The following required settings are missing from the \"{file_name}\" file:")
            # Log the list of missing required settings
            for setting in settings_missing:
                logging.critical(f"- \"{setting.lower()}\"")
            logging.critical( "-")
            logging.critical( "- Please edit the settings file as needed and restart the program")
            print( "-")
            print( "-")
            print( "- If you type \"new\" and press Enter:")
            print( "- A clean settings file will be generated and opened, and")
            print( "- the old file will be renamed with \"_old\" at the end and opened too")
            print("-")
            choice = input("Type \"new\" and press Enter, or just press Enter to exit...")

            if "new" in choice:
                settings_default_init(file_name, default_file_path)
            else:
                exit()

        # Check if the PES download folder location contains the magic number ** and replace it with the pes version
        pes_folder_path = os.environ.get("PES_FOLDER_PATH", 'unknown')
        if "**" in pes_folder_path:
            os.environ["PES_FOLDER_PATH"] = pes_folder_path.replace("**", os.environ["PES_VERSION"])

        # Prepare the path to the PES exe in the parent folder of the PES download folder
        pes_exe_name = "PES20" + os.environ["PES_VERSION"] + ".exe"
        os.environ["PES_EXE_PATH"] = os.path.join(os.environ["PES_FOLDER_PATH"], pes_exe_name)