import os
import sys
import stat
import py7zr
import shutil
import logging

from .APP_DATA import (
    APP_OWNER,
    APP_NAME,
    APP_VERSION_MAJOR,
    APP_VERSION_MINOR,
    APP_VERSION_PATCH,
)
from .pausing import pause
from .version_downloading import version_download
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
    app_version = f"{APP_VERSION_MAJOR}.{APP_VERSION_MINOR}.{APP_VERSION_PATCH}"

    # Create a "temp" folder inside "Engines"
    temp_folder_path = os.path.join("Engines", "temp")

    if not os.path.exists(temp_folder_path):
        os.makedirs(temp_folder_path)

    print("-")
    print(f"- Downloading and unpacking version {app_version}...")

    # Download the current version
    pack_name = version_download(APP_OWNER, APP_NAME, app_version, "7z", temp_folder_path)

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

    app_name_full = APP_NAME + " " + app_version
    app_full_folder = os.path.join(temp_folder_path, app_name_full)

    file_path_new = os.path.join(app_full_folder, file_path)

    if not os.path.exists(file_path_new):

        logging.critical( "-")
        logging.critical( "- FATAL ERROR - File not found in the clean package:")
        logging.critical(f"- \"{file_path_new}\"")
        logging.critical( "-")
        logging.critical( "- Please report this error to the developer by posting the \"issues.log\" file")

        pause("- Press Enter to exit... ", force=True)

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
        app_version = f"{APP_VERSION_MAJOR}.{APP_VERSION_MINOR}.{APP_VERSION_PATCH}"
        title_string = f"- 4cc aet compiler Red {app_version}"

        logging.basicConfig(filename="issues.log", level=logging.CRITICAL, filemode='w', format="%(message)s")
        logging.critical(title_string)
        logging.critical("-")
        logging.critical("- Library file not found, self healing failed or not attempted.")
        logging.critical(module_exception)

        sys.exit()

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

        pause(force=True)

    if not file_healed:
        logger_stop()
        sys.exit()


def remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except PermissionError:
        print( "-")
        logging.error( "- ERROR - Permission error")
        if os.path.isfile(path):
            logging.error(f"- File path: {path}")
            pause("- Close the file if open and press Enter to try again... ")
        else:
            logging.error(f"- Folder path: {path}")
            pause("- Close any opened files from the folder and press Enter to try again... ")
        print( "-")
        remove_readonly(func, path, _)

def readonlybit_remove_tree(path):
    "Clear the readonly bit on an entire tree"
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, 0o600)
        for name in dirs:
            filename = os.path.join(root, name)
            os.chmod(filename, 0o700)
        for dir in dirs:
            readonlybit_remove_tree(os.path.join(root, dir))

def get_files_list(folder_path, recursive=False):
    """
    Get a list of files in the folder indicated.

    Args:
        folder_path: Path to the folder
        recursive: If True, include files in subdirectories with relative paths

    Returns:
        List of filenames (or relative paths if recursive=True)
    """
    if not os.path.exists(folder_path):
        return []

    files_list = []
    if recursive:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # Get relative path from folder_path
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, folder_path)
                # Use forward slashes for consistency
                rel_path = rel_path.replace('\\', '/')
                files_list.append(rel_path)
    else:
        for item in os.listdir(folder_path):
            src_path = os.path.join(folder_path, item)
            if os.path.isfile(src_path):
                files_list.append(item)

    return files_list


def move_files_to_windx11(source_dir: str, target_base_path: str, use_sourceimages: bool = True):
    """
    Move files from source directory to target path with windx11 subfolder structure.

    Args:
        source_dir: Source directory containing files
        target_base_path: Base target path where files will be moved with #windx11 structure
        use_sourceimages: Whether the path should include sourceimages or not
    """

    terminal_name = "sourceimages/#windx11" if use_sourceimages else "#windx11"

    # Create a terminal subfolder for the root
    subfolder = os.path.join(target_base_path, terminal_name)
    if not os.path.exists(subfolder):
        os.makedirs(subfolder)

    # Create a terminal subfolder for every subfolder in the source directory
    for root, dirs, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)
        if rel_path != '.':
            target_subfolder = os.path.join(target_base_path, rel_path, terminal_name)
            if not os.path.exists(target_subfolder):
                os.makedirs(target_subfolder)

    # Move the files to their corresponding subfolders
    for root, dirs, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)
        if rel_path == '.':
            target_folder = subfolder
        else:
            target_folder = os.path.join(target_base_path, rel_path, terminal_name)

        for file in files:
            # First delete if it already exists
            if os.path.exists(os.path.join(target_folder, file)):
                os.remove(os.path.join(target_folder, file))

            shutil.move(os.path.join(root, file), target_folder)
