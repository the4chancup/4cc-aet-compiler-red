import os
import stat
import shutil
import logging

from .lib.bins_update import bins_pack
from .lib.contents_packing import contents_pack
from .lib.utils.pausing import pause
from .lib.utils.logging_tools import logger_stop
from .lib.utils.FILE_INFO import (
    EXTRACTED_TEAMS_PATH,
    EXTRACTED_REFEREES_PATH,
    PATCHES_CONTENTS_PATH,
    REFS_TEMPLATE_PREFOX_PATH,
    REFS_TEMPLATE_FOX_PATH,
)


def remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)
    func(path)


def contents_from_extracted():

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    multicpk_mode = int(os.environ.get('MULTICPK_MODE', '0'))
    bins_updating = int(os.environ.get('BINS_UPDATING', '0'))

    # Verify that the input folder exists, stop the program otherwise
    if all([
        not os.path.exists(EXTRACTED_TEAMS_PATH),
        not os.path.exists(EXTRACTED_REFEREES_PATH)
    ]):

        logging.critical( "-")
        logging.critical( "- FATAL ERROR - No \"extracted\" input folder found")
        logging.critical( "-")
        logging.critical( "- Please do not run this script before running the previous ones")
        logger_stop()

        print( "-")
        pause("Press any key to exit... ")

        exit()

    # Check the presence of the folders
    refs_present = os.path.exists(EXTRACTED_REFEREES_PATH)
    teams_present = os.path.exists(EXTRACTED_TEAMS_PATH)

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
        refs_template_path = REFS_TEMPLATE_FOX_PATH if fox_mode else REFS_TEMPLATE_PREFOX_PATH
        refs_template_name = os.path.basename(refs_template_path)
        if os.path.exists(refs_template_path):
            print(f"- Copying referee base files from {refs_template_name}")
            for item in os.listdir(refs_template_path):
                src_path = os.path.join(refs_template_path, item)
                dst_path = os.path.join(refs_folder_path, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
        else:
            logging.error( "- ERROR - Refs template folder not found")
            logging.error(f"- Folder path: {refs_template_path}")

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
        contents_pack(EXTRACTED_TEAMS_PATH, faces_folder_name, uniform_folder_name)

        # Delete the "extracted" folder
        if os.path.exists(EXTRACTED_TEAMS_PATH):
            shutil.rmtree(EXTRACTED_TEAMS_PATH, onexc=remove_readonly)

    if refs_present:
        # Pack the referees' contents
        contents_pack(EXTRACTED_REFEREES_PATH, refs_folder_name, refs_folder_name)

        # Delete the "extracted" folder
        if os.path.exists(EXTRACTED_REFEREES_PATH):
            shutil.rmtree(EXTRACTED_REFEREES_PATH, onexc=remove_readonly)


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
