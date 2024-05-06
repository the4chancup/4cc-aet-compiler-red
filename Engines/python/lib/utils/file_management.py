import os
import sys
import py7zr
import shutil
import logging

from . import APP_DATA
from .update_check import update_check
from .update_check import version_download


def file_heal(file_path):
    """
    Check the current version, download the latest version, unpack and copy a file, and delete temporary files.

    Args:
        file_path (str): The path to the file to copy and delete.

    Returns:
        bool: True if the file was copied successfully, False otherwise.
    """

    # Check if the current version is the latest
    update_available = update_check(APP_DATA.OWNER, APP_DATA.NAME, APP_DATA.VERSION_MAJOR, APP_DATA.VERSION_MINOR, APP_DATA.VERSION_PATCH, check_force=True)

    if update_available is not False:
        return False

    # Prepare the version string
    version_last = f"{APP_DATA.VERSION_MAJOR}.{APP_DATA.VERSION_MINOR}.{APP_DATA.VERSION_PATCH}"

    # Create a "temp" folder inside "Engines"
    temp_folder_path = os.path.join("Engines", "temp")

    if not os.path.exists(temp_folder_path):
        os.makedirs(temp_folder_path)

    print("-")
    print("- Downloading and unpacking...")

    # Download the latest version
    pack_name = version_download(APP_DATA.OWNER, APP_DATA.NAME, version_last, "7z", temp_folder_path)

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

    app_name_full = APP_DATA.NAME + " " + version_last
    app_full_folder = os.path.join(temp_folder_path, app_name_full)

    file_path_new = os.path.join(app_full_folder, file_path)

    if not os.path.exists(file_path_new):

        logging.critical( "-")
        logging.critical( "- FATAL ERROR - File not found in the clean package:")
        logging.critical(f"- \"{file_path_new}\"")
        logging.critical( "- Please report this error to the developer by posting the \"issues.log\" file")

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
    print( "- If you're on the latest version, you can type \"heal\" to have")
    print( "- the compiler download a clean package and recover the file automatically")

    while True:
        print( "-")
        response = input("Type \"heal\" and press Enter, or just press Enter to exit...")

        if not response:
            exit()

        if "heal" in response:
            # Run the self-healing script
            file_healed = file_heal(file_path)
            break
        else:
            print( "-")
            print( "- Try again")

    return file_healed


def module_heal_offer(module_exception):

    # Get the path to the module from the exception string
    # "No module named 'folder.module'"
    module_path_raw = module_exception.args[0][17:].strip("'")
    module_path = module_path_raw.replace(".", "\\") + ".py"

    file_path = os.path.join("Engines", module_path)

    file_healed = file_heal_offer(file_path)

    return file_healed


def file_critical_check(file_path, healing_allowed = True):

    if os.path.exists(file_path):
        return

    file_healed = False

    logging.critical( "-")
    logging.critical(f"- FATAL ERROR - Missing \"{file_path}\" file")
    print( "-")
    print( "- Please grab it from the compiler's original 7z package")

    if healing_allowed and sys.platform == "win32":

        file_healed = file_heal_offer(file_path)

    if not file_healed:
        print( "-")
        print( "- The program will now close")
        print( "-")
        input("Press Enter to continue...")

        exit()
