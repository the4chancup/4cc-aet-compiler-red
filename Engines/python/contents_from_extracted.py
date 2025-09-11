import os
import stat
import shutil
import logging

from .lib.bins_update import bins_pack
from .lib.contents_packing import contents_pack
from .lib.utils.pausing import pause
from .lib.utils.logging_tools import logger_stop
from .lib.utils.FILE_INFO import (
    EXTRACTED_PATH,
    PATCHES_CONTENTS_PATH,
    PATCHES_CONTENTS_REFS_PATH,
)


def remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)
    func(path)


def contents_from_extracted():

    # Read the necessary parameters
    multicpk_mode = int(os.environ.get('MULTICPK_MODE', '0'))
    bins_updating = int(os.environ.get('BINS_UPDATING', '0'))

    # Verify that the input folder exists, stop the program otherwise
    if not os.path.exists(EXTRACTED_PATH):

        logging.critical( "-")
        logging.critical( "- FATAL ERROR - Input folder not found")
        logging.critical(f"- Missing folder: {EXTRACTED_PATH}")
        logging.critical( "-")
        logging.critical( "- Please do not run this script before running the previous ones")
        logger_stop()

        print( "-")
        pause("Press any key to exit... ")

        exit()

    # Check the items in the extracted folder
    refs_present = False
    teams_present = False
    for item_folder in os.listdir(EXTRACTED_PATH):
        if item_folder == "Referees":
            refs_present = True
        else:
            teams_present = True

    # Set the name for the folders to put stuff into
    if not multicpk_mode:

        faces_folder_name = "Singlecpk"
        uniform_folder_name = "Singlecpk"
        bins_folder_name = "Singlecpk"

    else:

        faces_folder_name = "Facescpk"
        uniform_folder_name = "Uniformcpk"
        bins_folder_name = "Binscpk"

    refs_folder_name = "Refscpk"


    print("-")
    print("- Preparing the patch folders")
    print("-")


    if refs_present:
        # Delete the contents folder
        refs_folder_path = os.path.join(PATCHES_CONTENTS_PATH, refs_folder_name)
        if os.path.exists(refs_folder_path):
            shutil.rmtree(refs_folder_path, onexc=remove_readonly)

        # Create the folder
        os.makedirs(refs_folder_path, exist_ok=True)

        # Copy patches_contents_refs
        if os.path.exists(PATCHES_CONTENTS_REFS_PATH):
            print("- Copying referee base files from patches_contents_refs")
            for item in os.listdir(PATCHES_CONTENTS_REFS_PATH):
                src_path = os.path.join(PATCHES_CONTENTS_REFS_PATH, item)
                dst_path = os.path.join(refs_folder_path, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)

    if teams_present:
        # Create folders just in case
        faces_folder_path = os.path.join(PATCHES_CONTENTS_PATH, faces_folder_name)
        uniform_folder_path = os.path.join(PATCHES_CONTENTS_PATH, uniform_folder_name)
        os.makedirs(faces_folder_path, exist_ok=True)
        os.makedirs(uniform_folder_path, exist_ok=True)


    # If Bins Updating is enabled
    if teams_present and bins_updating:

        print("-")
        print("- Bins Updating is enabled")
        print("-")

        # Update the bins
        bins_pack(bins_folder_name)


    if teams_present:
        # Pack the teams' contents
        contents_pack(EXTRACTED_PATH, faces_folder_name, uniform_folder_name)

    if refs_present:
        # Pack the referees' contents
        extracted_refs_path = os.path.join(EXTRACTED_PATH, "Referees")
        contents_pack(extracted_refs_path, refs_folder_name, refs_folder_name)

    # Finally delete the "extracted" folder
    if os.path.exists(EXTRACTED_PATH):
        shutil.rmtree(EXTRACTED_PATH, onexc=remove_readonly)


    if 'all_in_one' in os.environ:

        print('-')
        print('- Patch contents folder prepared')
        print('-')

    else:

        print('-')
        print('- The patches_contents folder has been prepared')
        print('-')
        print('- 4cc aet compiler by Shakes')
        print('-')
