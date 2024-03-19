import os
import configparser
import shutil


def settings_missing():

    # Check if all the necessary settings are set
    required_settings = ['pes_version',
                         'cpk_name',
                         'move_cpks',
                         'pes_download_folder_location',
                         'bins_updating',
                         'fmdl_id_editing',
                         'multicpk_mode',
                         'faces_cpk_name',
                         'uniform_cpk_name',
                         'bins_cpk_name',
                         'pause_when_wrong',
                         'pass_through',
                         'admin_mode']

    settings_missing = [setting for setting in required_settings if setting not in os.environ]

    return settings_missing


def settings_default_init(file_path):

    # Grab the extension of the file
    file_extension = os.path.splitext(file_path)[1]

    # Prepare the name of the default settings file, with "_default" appended
    default_file_name = os.path.basename(file_path).replace(file_extension, "_default" + file_extension)

    # Prepare the path to the default settings file inside the Engines folder
    default_file_path = os.path.join(os.path.dirname(file_path), "Engines", default_file_name)

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
        
        # Open it in an external text editor
        os.startfile(old_file_name)

    # Copy the default settings file to the main folder, with the original name
    shutil.copy(default_file_path, file_path)

    # Open the settings file in an external text editor
    os.startfile(file_path)

    # Exit the script
    exit()


def settings_init(file_name):

    # Check if the file exists
    if not os.path.isfile(file_name):

        print("- Warning:")
        print(f"- The {file_name} file is missing.")
        print("-")
        print("- A clean settings file will be generated and opened.")
        print("- Please edit the settings as needed and restart the program.")
        print("-")
        input("Press Enter to continue...")

        settings_default_init(file_name)

    else:

        # Read the settings
        config = configparser.ConfigParser()
        config.read(file_name)

        for section in config.sections():
            for key, value in config.items(section):
                os.environ[key] = value

        # Check if any settings are missing
        if settings_missing():

            print("- Warning:")
            print(f"- Some settings are missing from the {file_name} file:")
            # Print the list of missing settings
            print("- " + "\n- ".join(settings_missing()))
            print("-")
            print("- A clean settings file will be generated and opened.")
            print("- The old file will be renamed with _old at the end and opened too.")
            print("- Please edit the settings as needed and restart the program.")
            print("-")
            input("Press Enter to continue...")

            settings_default_init(file_name)
