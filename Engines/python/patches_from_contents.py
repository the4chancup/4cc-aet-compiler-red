import os
import shutil
import logging
import subprocess

from .lib import pes_cpk_pack as cpktool
from .lib.utils import COLORS
from .lib.utils.pausing import pause
from .lib.utils.logging_tools import logger_stop
from .lib.utils.app_tools import log_presence_warn
from .lib.utils.FILE_INFO import (
    PATCHES_CONTENTS_PATH,
    PATCHES_OUTPUT_PATH,
)


def patches_from_contents():

    # Read the necessary parameters
    all_in_one = int(os.environ.get('ALL_IN_ONE', '0'))
    pes_version = int(os.environ.get('PES_VERSION', '19'))
    move_cpks = int(os.environ.get('MOVE_CPKS', '0'))
    pes_folder_path = os.environ.get('PES_FOLDER_PATH', 'unknown')
    run_pes = int(os.environ.get('RUN_PES', '0'))
    bins_updating = int(os.environ.get('BINS_UPDATING', '0'))

    refs_mode = int(os.environ.get('REFS_MODE', '0'))
    multicpk_mode = int(os.environ.get('MULTICPK_MODE', '0'))
    cpk_name = os.environ.get('CPK_NAME', '4cc_69_midcup')
    faces_cpk_name = os.environ.get('FACES_CPK_NAME', '4cc_40_faces')
    uniform_cpk_name = os.environ.get('UNIFORM_CPK_NAME', '4cc_45_uniform')
    bins_cpk_name = os.environ.get('BINS_CPK_NAME', '4cc_08_bins')
    refs_cpk_name = os.environ.get('REFS_CPK_NAME', '4cc_35_referees')
    cache_clear = int(os.environ.get('CACHE_CLEAR', '0'))

    pes_download_path = os.path.join(pes_folder_path, "download")

    # Create output folder just in case
    os.makedirs(PATCHES_OUTPUT_PATH, exist_ok=True)

    # Set the names for the folders to put stuff into and for the cpks
    if refs_mode:
        folder_name_list = ["Refscpk"]
        cpk_name_list = [refs_cpk_name]
    elif not multicpk_mode:
        folder_name_list = ["Singlecpk"]
        cpk_name_list = [cpk_name]
    else:
        folder_name_list = ["Facescpk", "Uniformcpk"]
        cpk_name_list = [faces_cpk_name, uniform_cpk_name]

        if bins_updating:
            folder_name_list.append("Binscpk")
            cpk_name_list.append(bins_cpk_name)

    # Make the patches
    cpk_string = "cpk" if not multicpk_mode else "cpks"
    print( "-")
    print(f"- Packing the {cpk_string}...")

    for folder_name, cpk_name in zip(folder_name_list, cpk_name_list):

        folder_path = os.path.join(PATCHES_CONTENTS_PATH, folder_name)

        # Verify that the input folder exists, stop the program otherwise
        if not os.path.exists(folder_path):

            logging.critical( "-")
            logging.critical( "- FATAL ERROR - Input folder not found")
            logging.critical(f"- Missing folder: {folder_path}")
            logging.critical( "-")
            logging.critical( "- Please do not run this script before running the previous ones")
            logger_stop()

            print( "-")
            pause("Press any key to exit... ")

            exit()

        # Make sure that the folder is not empty to avoid errors
        if not os.listdir(folder_path):
            open(os.path.join(folder_path, 'placeholder'), 'w').close()

        source_contents_path_list = [os.path.join(folder_path, x) for x in os.listdir(folder_path)]
        cpk_path = os.path.join(PATCHES_OUTPUT_PATH, f"{cpk_name}.cpk")

        cpktool.main(cpk_path, source_contents_path_list, True)

    # Delete the patches contents folder
    if cache_clear:
        shutil.rmtree(PATCHES_CONTENTS_PATH)

    print("-")
    print("- The patches have been created")

    # If Move Cpks mode is enabled
    if move_cpks:

        print("-")
        print("- Move Cpks mode is enabled")
        print("-")
        print("- Moving the cpks to the download folder")

        for cpk_name in cpk_name_list:
            cpk_destination_path = os.path.join(pes_download_path, f"{cpk_name}.cpk")

            # Remove the cpk from the destination folder if present
            if os.path.exists(cpk_destination_path):
                try:
                    os.remove(cpk_destination_path)

                except PermissionError:
                    logging.critical( "-")
                    logging.critical( "- FATAL ERROR - Error while trying to remove the old cpk")
                    logging.critical(f"- Path:           {cpk_destination_path}")
                    logging.critical( "- Please check if PES is open, and close it if so")

                    print( "-")
                    input("Press Enter to continue after checking... ")

                    try:
                        os.remove(cpk_destination_path)

                    except PermissionError:
                        logging.critical( "-")
                        logging.critical( "- FATAL ERROR - Cannot remove the old cpk")
                        logging.critical( "- Restart your PC and try again")
                        logger_stop()

                        print( "-")
                        pause("Press any key to exit... ")

                        exit()

            # Move the cpk to the destination folder
            cpk_path = os.path.join(PATCHES_OUTPUT_PATH, f"{cpk_name}.cpk")
            shutil.move(cpk_path, pes_download_path)

        print("-")
        print("- Done")
        print("-")

        # If Run PES mode is enabled, start the pes exe from PES_EXE_PATH
        if run_pes:

            pes_exe_path = os.environ.get('PES_EXE_PATH', 'null')

            if os.path.exists(pes_exe_path):
                print( "-")
                print(f"- Run PES mode is enabled, starting PES20{pes_version}...")
                subprocess.Popen([pes_exe_path], cwd=pes_folder_path)
            else:
                print( "-")
                print(f"- Run PES mode is enabled but the PES20{pes_version} exe was not found")
                print(f"- in the {pes_folder_path} folder")
                print( "- PES won't be started")

    if all_in_one:
        log_presence_warn()

        print( "-")
        print( "-")
        print(f"- 4cc aet compiler {COLORS.BRIGHT_RED}Red{COLORS.RESET} by Shakes")
        print( "-")
        print( "-")
