import os
import py7zr
import shutil
import logging

from . import APP_DATA
from .pausing import pause
from .update_check import version_download
from .logging_tools import logger_stop


def file_heal(file_path):
    """
    Download the current version, unpack and copy a file, and delete temporary files.

    Args:
        file_path (str): The path to the file to copy and delete.

    Returns:
        bool: True if the file was copied successfully, False otherwise.
    """

    # Prepare the version string
    app_version = f"{APP_DATA.VERSION_MAJOR}.{APP_DATA.VERSION_MINOR}.{APP_DATA.VERSION_PATCH}"

    # Create a "temp" folder inside "Engines"
    temp_folder_path = os.path.join("Engines", "temp")

    if not os.path.exists(temp_folder_path):
        os.makedirs(temp_folder_path)

    print("-")
    print(f"- Downloading and unpacking version {app_version}...")

    # Download the current version
    pack_name = version_download(APP_DATA.OWNER, APP_DATA.NAME, app_version, "7z", temp_folder_path)

    if pack_name is None:
        print("-")
        print("- Failed to download")

        return False

    pack_path = os.path.join(temp_folder_path, pack_name)

    # Unpack the 7z file to the parent folder using py7zr
    with py7zr.SevenZipFile(pack_path, mode="r") as archive:
        archive.extractall(temp_folder_path)

    # Delete the 7z file
    os.remove(pack_path)

    app_name_full = APP_DATA.NAME + " " + app_version
    app_full_folder = os.path.join(temp_folder_path, app_name_full)

    file_path_new = os.path.join(app_full_folder, file_path)

    if not os.path.exists(file_path_new):

        logging.critical( "-")
        logging.critical( "- FATAL ERROR - File not found in the clean package:")
        logging.critical(f"- \"{file_path_new}\"")
        logging.critical( "-")
        logging.critical( "- Please report this error to the developer by posting the \"issues.log\" file")
        print( "-")
        pause("- Press Enter to exit... ")

        success = False

    else:

        # Copy the file from its new location to its regular location
        shutil.copy(file_path_new, file_path)

        print( "-")
        print( "- File healed successfully")
        print( "-")

        success = True

    # Delete the "temp" folder
    shutil.rmtree(temp_folder_path)

    return success


def file_heal_offer(file_path):

    print( "-")
    print( "- You can also type \"heal\" to have the compiler download")
    print( "- a clean package and recover the file automatically")

    while True:
        print( "-")
        response = input("Type \"heal\" and press Enter, or just press Enter to exit...")

        if not response:
            file_healed = False
            break

        if "heal" in response:
            # Run the self-healing script
            file_healed = file_heal(file_path)
            break
        else:
            print( "-")
            print( "- Try again")

    return file_healed


def module_recover(module_exception):

    # Get the path to the module from the exception string
    # "No module named 'folder.module'"
    module_path_raw = module_exception.args[0][17:].strip("'")
    module_path = module_path_raw.replace(".", "\\") + ".py"

    file_path = os.path.join("Engines", module_path)

    print( "-")
    print( "- FATAL ERROR - Missing library file")
    print(f"- The file \"{file_path}\" is missing")
    print( "-")
    print( "- Please grab it from the compiler's original 7z package")

    file_healed = file_heal_offer(file_path)

    if not file_healed:
        # Log to file
        app_version = f"{APP_DATA.VERSION_MAJOR}.{APP_DATA.VERSION_MINOR}.{APP_DATA.VERSION_PATCH}"
        title_string = f"- 4cc aet compiler Red {app_version}"

        logging.basicConfig(filename="issues.log", level=logging.CRITICAL, filemode='w', format="%(message)s")
        logging.critical(title_string)
        logging.critical("-")
        logging.critical("- Library file not found, self healing failed or not attempted.")
        logging.critical(module_exception)

        exit()

    return file_healed


def file_critical_check(file_path, healing_allowed = True):

    if os.path.exists(file_path):
        return

    logging.critical( "-")
    logging.critical( "- FATAL ERROR - Missing vital file")
    logging.critical(f"- The file \"{file_path}\" is missing")
    print( "-")
    print( "- Please grab it from the compiler's original 7z package")

    if healing_allowed:

        file_healed = file_heal_offer(file_path)

    else:
        file_healed = False

        print( "-")
        print( "- The program will now close")
        print( "-")
        pause()

    if not file_healed:
        logger_stop()
        exit()
