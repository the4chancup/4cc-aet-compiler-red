import os
import shutil
import logging

from .lib.bins_update import bins_update
from .lib import pes_uniparam_edit as uniparamtool
from .lib.model_packing import models_pack
from .lib.cpk_tools import files_fetch_from_cpks
from .lib.utils.pausing import pause
from .lib.utils.logging_tools import logger_stop


def contents_from_extracted():

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    fox_19 = (int(os.environ.get('PES_VERSION', '19')) >= 19)

    multicpk_mode = int(os.environ.get('MULTICPK_MODE', '0'))
    bins_updating = int(os.environ.get('BINS_UPDATING', '0'))


    # Set the name for the folders to put stuff into
    if not multicpk_mode:

        faces_foldername = "Singlecpk"
        uniform_foldername = "Singlecpk"
        bins_foldername = "Singlecpk"

    else:

        faces_foldername = "Facescpk"
        uniform_foldername = "Uniformcpk"
        bins_foldername = "Binscpk"


    # Create folders just in case
    os.makedirs(f"./patches_contents/{faces_foldername}", exist_ok=True)
    os.makedirs(f"./patches_contents/{uniform_foldername}", exist_ok=True)


    print("-")
    print("- Preparing the patch folders")
    print("-")


    # If Bins Updating is enabled and there's an extracted_exports folder
    if bins_updating and os.path.exists("extracted_exports"):

        print("-")
        print("- Bins Updating is enabled")
        print("-")

        # Set the paths
        common_root_path = os.path.join("patches_contents", bins_foldername, "common")
        common_etc_path = os.path.join(common_root_path, "etc")
        uniform_team_path = os.path.join(common_root_path, "character0", "model", "character", "uniform", "team")

        # Prepare a list of sources and destination paths for the bin files
        bins_folder_path = "Engines/bins/temp"

        teamcolor_bin_path = os.path.join(bins_folder_path, "TeamColor.bin")
        kitcolor_bin_path = os.path.join(bins_folder_path, "UniColor.bin")

        bin_info_list = [
            {
                'source_path': "common/etc/TeamColor.bin",
                'destination_path': teamcolor_bin_path
            },
            {
                'source_path': "common/character0/model/character/uniform/team/UniColor.bin",
                'destination_path': kitcolor_bin_path
            },
        ]

        if fox_mode:
            # Set the filename depending on pes version
            uniparam_name = "UniformParameter19.bin" if fox_19 else "UniformParameter18.bin"

            uniparam_bin_path = os.path.join(bins_folder_path, uniparam_name)

            bin_info_list.append(
                {
                    'source_path': "common/character0/model/character/uniform/team/UniformParameter.bin",
                    'destination_path': uniparam_bin_path
                }
            )

        # Create the folders
        os.makedirs(common_etc_path, exist_ok=True)
        os.makedirs(uniform_team_path, exist_ok=True)
        os.makedirs(bins_folder_path, exist_ok=True)

        # Fetch the bin files from the cpks in the download folder and update their values
        bin_cpk_names_list = ['midcup', 'bins']
        files_fetch_from_cpks(bin_info_list, bin_cpk_names_list)

        bins_update(teamcolor_bin_path, kitcolor_bin_path)

        # And copy them to the Bins cpk folder
        shutil.copy(teamcolor_bin_path, common_etc_path)
        shutil.copy(kitcolor_bin_path, uniform_team_path)

        # If fox mode is enabled and there's a Kit Configs folder
        itemfolder_path = os.path.join("extracted_exports", "Kit Configs")
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
            uniparam_error = uniparamtool.main(uniparam_bin_path, kit_config_path_list, [], uniparam_bin_path, True)

            if uniparam_error:
                logging.critical("-")
                logging.critical("- FATAL ERROR - Error compiling the UniformParameter file")
                logging.critical("- The compiler will stop here because the cpk generated would crash PES")
                logging.critical("- Disable Bins Updating on the settings file and try again")
                logging.critical("-")
                logging.critical("- Please report this issue to the developer")
                logger_stop()

                print("-")
                pause("Press any key to exit... ")

                exit()

            # Copy the uniparam to the the Bins cpk folder with the proper filename
            shutil.copy(uniparam_bin_path, f"{uniform_team_path}/UniformParameter.bin")

            print("-")

        # Delete the bins folder
        shutil.rmtree(bins_folder_path)

    faces_folder_path = os.path.join("./patches_contents", faces_foldername)

    # Packing the face folders if 'Faces' directory exists
    main_dir = "./extracted_exports/Faces"
    if os.path.exists(main_dir):

        print("- \n- Packing the face folders")

        models_pack('face', main_dir, 'face/real', faces_folder_path)


    # Moving the kit configs if 'Kit Configs' directory exists
    main_dir = "./extracted_exports/Kit Configs"
    if os.path.exists(main_dir):
        print("- \n- Moving the kit configs")

        items_dir = f"./patches_contents/{uniform_foldername}/common/character0/model/character/uniform/team"

        # Create a "team" folder if needed
        os.makedirs(items_dir, exist_ok=True)

        # Move the kit configs to the Uniform cpk folder
        for item in os.listdir(main_dir):
            item_path = os.path.join(main_dir, item)
            target_item_path = os.path.join(items_dir, item)

            # If the target item path exists, remove it
            if os.path.exists(target_item_path):
                shutil.rmtree(target_item_path)

            # Move the item to the target directory
            shutil.move(item_path, items_dir)

        # Delete the main 'Kit Configs' folder
        if os.path.exists(main_dir):
            shutil.rmtree(main_dir)


    # If there's a Kit Textures folder, move its stuff
    main_dir = "./extracted_exports/Kit Textures"
    if os.path.exists(main_dir):
        print("- \n- Moving the kit textures")

        items_dir = (
            f"./patches_contents/{uniform_foldername}/common/character0/model/character/uniform/texture" if not fox_mode
            else f"./patches_contents/{uniform_foldername}/Asset/model/character/uniform/texture/#windx11"
        )

        # Create a texture folder if needed
        os.makedirs(items_dir, exist_ok=True)

        # Move the kit textures to the Uniform cpk folder
        for item in os.listdir(main_dir):
            item_path = os.path.join(main_dir, item)
            target_item_path = os.path.join(items_dir, item)

            # If the target item path exists, remove it
            if os.path.exists(target_item_path):
                os.remove(target_item_path)

            # Move the item to the target directory
            shutil.move(item_path, items_dir)

        # Delete the main 'Kit Textures' folder
        if os.path.exists(main_dir):
            shutil.rmtree(main_dir)


    # If there's a Boots folder, move or pack its stuff
    main_dir = "./extracted_exports/Boots"
    if os.path.exists(main_dir):

        if not fox_mode:
            print('-')
            print('- Moving the boots')
        else:
            print('-')
            print('- Packing the boots folders')

        models_pack('boots', main_dir, 'boots', faces_folder_path)

    # If there's a Gloves folder, move its stuff
    main_dir = "./extracted_exports/Gloves"
    if os.path.exists(main_dir):

        if not fox_mode:
            print('-')
            print('- Moving the gloves')
        else:
            print('-')
            print('- Packing the gloves folders')

        models_pack('glove', main_dir, 'glove', faces_folder_path)


    other_message = False

    # If there's a Collars folder, move its stuff
    main_dir = "./extracted_exports/Collars"
    if os.path.exists(main_dir):

        if not other_message:
            other_message = True

            print('-')
            print('- Moving the other stuff')

        items_folder_path = (
            'common/character0/model/character/uniform/nocloth' if not fox_mode
            else 'Asset/model/character/uniform/nocloth/#Win'
        )

        # Create a "collars" folder if needed
        items_folder_path_full = os.path.join('patches_contents', faces_foldername, items_folder_path)
        if not os.path.exists(items_folder_path_full):
            os.makedirs(items_folder_path_full)

        # Move the collars to the Faces cpk folder
        for item in os.listdir(main_dir):
            shutil.move(os.path.join(main_dir, item), items_folder_path_full)

        # Then delete the main folder
        shutil.rmtree(main_dir)


    # If there's a Portraits folder, move its stuff
    main_dir = os.path.join('extracted_exports', 'Portraits')
    if os.path.exists(main_dir):

        if not other_message:
            other_message = True

            print('-')
            print('- Moving the other stuff')

        # Create a "player" folder if needed
        items_folder_path_full = os.path.join('patches_contents', faces_foldername, 'common/render/symbol/player')
        if not os.path.exists(items_folder_path_full):
            os.makedirs(items_folder_path_full)

        # Move the portraits to the Faces cpk folder
        for item in os.listdir(main_dir):
            # First delete if it already exists
            if os.path.exists(os.path.join(items_folder_path_full, item)):
                os.remove(os.path.join(items_folder_path_full, item))

            shutil.move(os.path.join(main_dir, item), items_folder_path_full)

        # Then delete the main folder
        shutil.rmtree(main_dir)


    # If there's a Logo folder, move its stuff
    main_dir = os.path.join('extracted_exports', 'Logo')
    if os.path.exists(main_dir):

        if not other_message:
            other_message = True

            print('-')
            print('- Moving the other stuff')

        # Create a "flag" folder if needed
        items_folder_path_full = os.path.join('patches_contents', uniform_foldername, 'common/render/symbol/flag')
        if not os.path.exists(items_folder_path_full):
            os.makedirs(items_folder_path_full)

        # Move the logos to the Uniform cpk folder
        for item in os.listdir(main_dir):
            # First delete if it already exists
            if os.path.exists(os.path.join(items_folder_path_full, item)):
                os.remove(os.path.join(items_folder_path_full, item))

            shutil.move(os.path.join(main_dir, item), items_folder_path_full)

        # Then delete the main folder
        shutil.rmtree(main_dir)


    # Set the common folder path depending on the fox mode setting
    if not fox_mode:
        common_path = 'common/character1/model/character/uniform/common'
    else:
        common_path = 'Asset/model/character/common'

    # If there's a Common folder, move its stuff
    main_dir = 'extracted_exports/Common'
    if os.path.exists(main_dir):

        if not other_message:
            other_message = True

            print('-')
            print('- Moving the other stuff')

        # Create a "common" folder if needed
        items_folder_path_full = os.path.join('patches_contents', faces_foldername, common_path)
        if not os.path.exists(items_folder_path_full):
            os.makedirs(items_folder_path_full)

        # Move the team folders to the Faces cpk folder
        for item in os.listdir(main_dir):

            if not fox_mode:

                # If the folder already exists, delete it
                if os.path.exists(os.path.join(items_folder_path_full, item)):
                    shutil.rmtree(os.path.join(items_folder_path_full, item))

                # Move the folder
                shutil.move(os.path.join(main_dir, item), items_folder_path_full)

            else:

                # Create a team subfolder
                subfolder = os.path.join(items_folder_path_full, item, 'sourceimages/#windx11')
                if not os.path.exists(subfolder):
                    os.makedirs(subfolder)

                # Move the files inside the folder to the subfolder
                for subitem in os.listdir(os.path.join(main_dir, item)):
                    # First delete if it already exists
                    if os.path.exists(os.path.join(subfolder, subitem)):
                        os.remove(os.path.join(subfolder, subitem))

                    shutil.move(os.path.join(main_dir, item, subitem), subfolder)

        # Then delete the main folder
        shutil.rmtree(main_dir)


    # Finally delete the extracted exports folder
    if os.path.exists('./extracted_exports'):
        shutil.rmtree('./extracted_exports')


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
