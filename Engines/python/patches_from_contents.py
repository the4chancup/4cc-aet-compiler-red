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

    # Set the name for the folders to put stuff into
    if not multicpk_mode:

        faces_foldername = "Singlecpk"
        uniform_foldername = "Singlecpk"
        bins_foldername = "Singlecpk"

    else:

        faces_foldername = "Facescpk"
        uniform_foldername = "Uniformcpk"
        bins_foldername = "Binscpk"

    # Verify that the input folders exist, stop the program otherwise
    if (not os.path.exists(f"./patches_contents/{faces_foldername}") or
            not os.path.exists(f"./patches_contents/{uniform_foldername}") or
            (not os.path.exists(f"./patches_contents/{bins_foldername}") and bins_updating)):

        logging.critical("- FATAL ERROR - Input folder \"patches_contents\" not found")
        logging.critical("- Either this folder or one of its subfolders does not exist")
        logging.critical("-")
        logging.critical("- Please do not run this script before running the previous ones")
        logging.critical("-")

        return

    # Create output folder just in case
    os.makedirs("./patches_output", exist_ok=True)


    # Make the patches
    if multicpk_mode:

        # Make sure that the folders are not empty to avoid errors
        if not os.listdir(f"./patches_contents/{faces_foldername}"):
            open(f"./patches_contents/{faces_foldername}/placeholder", 'w').close()
        if not os.listdir(f"./patches_contents/{uniform_foldername}"):
            open(f"./patches_contents/{uniform_foldername}/placeholder", 'w').close()
        if bins_updating and not os.listdir(f"./patches_contents/{bins_foldername}"):
            open(f"./patches_contents/{bins_foldername}/placeholder", 'w').close()


        # Make the Faces patch (faces, portraits)
        print("-")
        print("- Packing the Faces patch")

        source_path = os.path.join("patches_contents", f"{faces_foldername}")
        source_contents_path_list = [os.path.join(source_path, x) for x in os.listdir(source_path)]
        destination_path = os.path.join("patches_output", f"{faces_cpk_name}.cpk")

        cpktool.main(destination_path, source_contents_path_list, True)

        # Make the Uniform patch (kits, logos, boots, gloves, etc.)
        print("-")
        print("- Packing the Uniform patch")

        source_path = os.path.join("patches_contents", f"{uniform_foldername}")
        source_contents_path_list = [os.path.join(source_path, x) for x in os.listdir(source_path)]
        destination_path = os.path.join("patches_output", f"{uniform_cpk_name}.cpk")

        cpktool.main(destination_path, source_contents_path_list, True)


        if bins_updating:

            # Make the Bins patch (unicolor, teamcolor)
            print("-")
            print("- Packing the Bins patch")

            source_path = os.path.join("patches_contents", f"{bins_foldername}")
            source_contents_path_list = [os.path.join(source_path, x) for x in os.listdir(source_path)]
            destination_path = os.path.join("patches_output", f"{bins_cpk_name}.cpk")

            cpktool.main(destination_path, source_contents_path_list, True)

    else:

        # Make sure that the folder is not empty to avoid errors
        if not os.listdir("./patches_contents/Singlecpk"):
            open("./patches_contents/Singlecpk/placeholder", 'w').close()


        # Make the single cpk patch
        print("-")
        print("- Packing the patch")

        source_path = os.path.join("patches_contents", "Singlecpk")
        source_contents_path_list = [os.path.join(source_path, x) for x in os.listdir(source_path)]
        destination_path = os.path.join("patches_output", f"{cpk_name}.cpk")

        cpktool.main(destination_path, source_contents_path_list, True)


    # Delete the contents folder
    if cache_clear:
        shutil.rmtree("./patches_contents")

    print("-")
    print("- The patches have been created")
    print("-")


    # If Move Cpks mode is enabled
    if move_cpks:

        print("- Move Cpks mode is enabled")
        print("-")
        print("- Moving the cpks to the download folder")
        print("-")

        if multicpk_mode:

            faces_cpk_path = os.path.join(pes_download_path, f"{faces_cpk_name}.cpk")
            uniform_cpk_path = os.path.join(pes_download_path, f"{uniform_cpk_name}.cpk")
            bins_cpk_path = os.path.join(pes_download_path, f"{bins_cpk_name}.cpk")

            # Remove the cpks from the destination folder if present
            if os.path.exists(faces_cpk_path):
                os.remove(faces_cpk_path)
            if os.path.exists(uniform_cpk_path):
                os.remove(uniform_cpk_path)
            if bins_updating:
                if os.path.exists(bins_cpk_path):
                    os.remove(bins_cpk_path)

            # Move the cpks to the destination folder
            shutil.move(f"patches_output/{faces_cpk_name}.cpk", pes_download_path)
            shutil.move(f"patches_output/{uniform_cpk_name}.cpk", pes_download_path)
            if bins_updating:
                shutil.move(f"patches_output/{bins_cpk_name}.cpk", pes_download_path)

        else:

            cpk_path = os.path.join(pes_download_path, f"{cpk_name}.cpk")

            # Remove the cpk from the destination folder if present
            if os.path.exists(cpk_path):
                os.remove(cpk_path)

            # Move the cpk to the destination folder
            shutil.move(f"patches_output/{cpk_name}.cpk", pes_download_path)

        print("- Done")
        print("-")

        # If Run PES mode is enabled, start the pes exe from PES_EXE_PATH
        if run_pes:

            pes_exe_path = os.environ.get('PES_EXE_PATH', 'null')

            if os.path.exists(pes_exe_path):
                print(f"- Run PES mode is enabled, starting PES20{pes_version}...")
                print( "-")
                subprocess.Popen([pes_exe_path], cwd=pes_folder_path)
            else:
                print(f"- Run PES mode is enabled but the PES20{pes_version} exe was not found")
                print(f"- in the {pes_folder_path} folder")
                print( "- PES won't be started")
                print( "-")


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
        print(f"- 4cc aet compiler {COLORS.BRIGHT_RED}Red{COLORS.RESET} by Shakes")
        print( "-")
        print( "-")
