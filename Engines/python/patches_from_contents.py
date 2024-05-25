import os
import shutil
import logging
import subprocess

from .lib import pes_cpk_pack as cpktool
from .lib.utils import COLORS


def patches_from_contents():

    # Read the necessary parameters
    all_in_one = int(os.environ.get('ALL_IN_ONE', '0'))
    pes_version = int(os.environ.get('PES_VERSION', '19'))
    move_cpks = int(os.environ.get('MOVE_CPKS', '0'))
    pes_folder_path = os.environ.get('PES_FOLDER_PATH', 'unknown')
    run_pes = int(os.environ.get('RUN_PES', '0'))
    bins_updating = int(os.environ.get('BINS_UPDATING', '0'))

    multicpk_mode = int(os.environ.get('MULTICPK_MODE', '0'))
    cpk_name = os.environ.get('CPK_NAME', '4cc_69_midcup')
    faces_cpk_name = os.environ.get('FACES_CPK_NAME', '4cc_40_faces')
    uniform_cpk_name = os.environ.get('UNIFORM_CPK_NAME', '4cc_45_uniform')
    bins_cpk_name = os.environ.get('BINS_CPK_NAME', '4cc_08_bins')
    cache_clear = int(os.environ.get('CACHE_CLEAR', '0'))

    pes_download_path = os.path.join(pes_folder_path, "download")

    # Create output folder just in case
    os.makedirs("./patches_output", exist_ok=True)

    # Set the names for the folders to put stuff into and for the cpks
    if not multicpk_mode:
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

        folder_path = os.path.join("patches_contents", folder_name)

        # Verify that the input folder exists, stop the program otherwise
        if not os.path.exists(folder_path):

            logging.critical( "-")
            logging.critical( "- FATAL ERROR - Input folder not found")
            logging.critical(f"- Missing folder: {folder_path}")
            logging.critical( "-")
            logging.critical( "- Please do not run this script before running the previous ones")

            return

        # Make sure that the folder is not empty to avoid errors
        if not os.listdir(folder_path):
            open(os.path.join(folder_path, 'placeholder'), 'w').close()

        source_contents_path_list = [os.path.join(folder_path, x) for x in os.listdir(folder_path)]
        cpk_path = os.path.join("patches_output", f"{cpk_name}.cpk")

        cpktool.main(cpk_path, source_contents_path_list, True)

    # Delete the contents folder
    if cache_clear:
        shutil.rmtree("./patches_contents")

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
                os.remove(cpk_destination_path)

            # Move the cpk to the destination folder
            cpk_path = os.path.join("patches_output", f"{cpk_name}.cpk")
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
        if os.path.exists("issues.log"):
            # Warn about there being some issues and about having to open the log
            print( "-")
            print(f"- {COLORS.DARK_YELLOW}Warning{COLORS.RESET}: There were some potential issues in the exports")
            print( "- Please check the issues.log file for more details")
        else:
            print( "-")
            print(f"- {COLORS.DARK_GREEN}No issues were found{COLORS.RESET}")

        if os.path.exists("suggestions.log"):
            # Warn about there being some suggestions
            print( "-")
            print(f"- {COLORS.DARK_CYAN}Info{COLORS.RESET}: There are some suggestions available")
            print( "- Check the suggestions.log file to improve your aesthetics")

        print( "-")
        print( "-")
        print(f"- 4cc aet compiler {COLORS.BRIGHT_RED}Red{COLORS.RESET} by Shakes")
        print( "-")
        print( "-")
