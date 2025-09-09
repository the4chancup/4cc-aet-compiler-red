import os
import stat
import shutil
import logging

from .lib.bins_update import bins_update
from .lib import pes_uniparam_edit as uniparamtool
from .lib.contents_packing import contents_pack
from .lib.cpk_tools import files_fetch_from_cpks
from .lib.utils.pausing import pause
from .lib.utils.logging_tools import logger_stop
from .lib.utils.FILE_INFO import (
    EXTRACTED_PATH,
    PATCHES_CONTENTS_PATH,
    PATCHES_CONTENTS_REFS_PATH,
    BIN_FOLDER_PATH,
    TEAMCOLOR_BIN_NAME,
    UNICOLOR_BIN_NAME,
    UNIPARAM_NAME,
    UNIPARAM_18_NAME,
    UNIPARAM_19_NAME,
)


def remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)
    func(path)


def contents_from_extracted():

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    fox_19 = (int(os.environ.get('PES_VERSION', '19')) >= 19)
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

        faces_foldername = "Singlecpk"
        uniform_foldername = "Singlecpk"
        bins_foldername = "Singlecpk"

    else:

        faces_foldername = "Facescpk"
        uniform_foldername = "Uniformcpk"
        bins_foldername = "Binscpk"

    refs_foldername = "Refscpk"

    bins_folder_path = os.path.join(PATCHES_CONTENTS_PATH, bins_foldername)
    refs_folder_path = os.path.join(PATCHES_CONTENTS_PATH, refs_foldername)

    print("-")
    print("- Preparing the patch folders")
    print("-")


    if refs_present:
        # Delete the contents folder
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
        os.makedirs(f"{PATCHES_CONTENTS_PATH}/{faces_foldername}", exist_ok=True)
        os.makedirs(f"{PATCHES_CONTENTS_PATH}/{uniform_foldername}", exist_ok=True)


    # If Bins Updating is enabled
    if teams_present and bins_updating:

        print("-")
        print("- Bins Updating is enabled")
        print("-")

        # Set the paths
        COMMON_ETC_PATH = "common/etc"
        UNIFORM_TEAM_PATH = "common/character0/model/character/uniform/team"

        patch_bins_common_etc_path = os.path.join(bins_folder_path, COMMON_ETC_PATH)
        patch_bins_uniform_team_path = os.path.join(bins_folder_path, UNIFORM_TEAM_PATH)

        # Prepare a list of sources and destination paths for the bin files
        BINS_TEMP_FOLDER_PATH = os.path.join(BIN_FOLDER_PATH, "temp")
        TEAMCOLOR_BIN_TEMP_PATH = os.path.join(BINS_TEMP_FOLDER_PATH, TEAMCOLOR_BIN_NAME)
        UNICOLOR_BIN_TEMP_PATH = os.path.join(BINS_TEMP_FOLDER_PATH, UNICOLOR_BIN_NAME)

        bin_info_list = [
            {
                'source_path': f"{COMMON_ETC_PATH}/{TEAMCOLOR_BIN_NAME}",
                'destination_path': TEAMCOLOR_BIN_TEMP_PATH,
                'fallback_path': f"{BIN_FOLDER_PATH}/{TEAMCOLOR_BIN_NAME}",
            },
            {
                'source_path': f"{UNIFORM_TEAM_PATH}/{UNICOLOR_BIN_NAME}",
                'destination_path': UNICOLOR_BIN_TEMP_PATH,
                'fallback_path': f"{BIN_FOLDER_PATH}/{UNICOLOR_BIN_NAME}",
            },
        ]

        if fox_mode:
            # Set the filename depending on pes version
            UNIPARAM_TEMP_NAME = UNIPARAM_19_NAME if fox_19 else UNIPARAM_18_NAME
            UNIPARAM_BIN_TEMP_PATH = os.path.join(BINS_TEMP_FOLDER_PATH, UNIPARAM_TEMP_NAME)

            bin_info_list.append(
                {
                    'source_path': f"{UNIFORM_TEAM_PATH}/{UNIPARAM_NAME}",
                    'destination_path': UNIPARAM_BIN_TEMP_PATH,
                    'fallback_path': f"{BIN_FOLDER_PATH}/{UNIPARAM_TEMP_NAME}",
                }
            )

        # Create the folders
        os.makedirs(patch_bins_common_etc_path, exist_ok=True)
        os.makedirs(patch_bins_uniform_team_path, exist_ok=True)
        os.makedirs(BINS_TEMP_FOLDER_PATH, exist_ok=True)

        # Fetch the bin files from the cpks in the download folder and update their values
        BIN_CPK_NAMES_LIST = ['midcup', 'bins']
        files_fetch_from_cpks(bin_info_list, BIN_CPK_NAMES_LIST)

        bins_update(TEAMCOLOR_BIN_TEMP_PATH, UNICOLOR_BIN_TEMP_PATH)

        # And copy them to the Bins cpk folder
        shutil.copy(TEAMCOLOR_BIN_TEMP_PATH, patch_bins_common_etc_path)
        shutil.copy(UNICOLOR_BIN_TEMP_PATH, patch_bins_uniform_team_path)

        # If fox mode is enabled and there's a Kit Configs folder
        itemfolder_path = os.path.join(EXTRACTED_PATH, "Kit Configs")
        if fox_mode and os.path.exists(itemfolder_path):

            print("- \n- Compiling the kit config files into the UniformParameter bin")

            # Prepare an array with all the kit config files inside each team folder in the Kit Configs folder
            kit_config_path_list = []
            for itemfolder_team in [f for f in os.listdir(itemfolder_path)]:
                itemfolder_team_path = os.path.join(itemfolder_path, itemfolder_team)

                # Add the path of each kit config file to the array
                for kit_config in [f for f in os.listdir(itemfolder_team_path) if f.endswith(".bin")]:
                    kit_config_path = os.path.join(itemfolder_team_path, kit_config)
                    kit_config_path_list.append(kit_config_path)

            # Compile the UniformParameter file
            uniparam_error = uniparamtool.main(UNIPARAM_BIN_TEMP_PATH, kit_config_path_list, [], UNIPARAM_BIN_TEMP_PATH, True)

            if uniparam_error:
                logging.critical("-")
                logging.critical("- FATAL ERROR - Error compiling the UniformParameter file")
                logging.critical("- The compiler will stop here because the generated cpk would crash PES")
                logging.critical("- Disable Bins Updating on the settings file and try again")
                logging.critical("-")
                logging.critical("- Please report this issue to the developer")
                logger_stop()

                print("-")
                pause("Press any key to exit... ")

                exit()

            # Copy the uniparam to the the Bins cpk folder with the proper filename
            shutil.copy(UNIPARAM_BIN_TEMP_PATH, f"{patch_bins_uniform_team_path}/{UNIPARAM_NAME}")

            print("-")

        # Delete the bins temp folder
        shutil.rmtree(BINS_TEMP_FOLDER_PATH, onexc=remove_readonly)

    # Pack the contents
    contents_pack(EXTRACTED_PATH, faces_foldername, uniform_foldername)

    if refs_present:
        # Pack the referees
        extracted_refs_path = os.path.join(EXTRACTED_PATH, "Referees")
        contents_pack(extracted_refs_path, refs_foldername, refs_foldername)

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
