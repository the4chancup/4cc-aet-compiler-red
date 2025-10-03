import os
import shutil

from .model_packing import models_pack
from .utils.file_management import remove_readonly
from .utils.FILE_INFO import (
    PATCHES_CONTENTS_PATH,
)


def contents_pack(extracted_path: str, faces_folder_name: str, uniform_folder_name: str):

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)

    faces_folder_path = os.path.join(PATCHES_CONTENTS_PATH, faces_folder_name)
    uniform_folder_path = os.path.join(PATCHES_CONTENTS_PATH, uniform_folder_name)

    refs_mode = extracted_path.endswith("referees")
    refs_string = "referee " if refs_mode else ""

    # Packing the face folders if 'Faces' directory exists
    main_dir = os.path.join(extracted_path, "Faces")
    if os.path.exists(main_dir):

        print(f"- \n- Packing the {refs_string}face folders")

        models_pack('face', main_dir, 'face/real', faces_folder_path)


    # Moving the kit configs if 'Kit Configs' directory exists
    main_dir = os.path.join(extracted_path, "Kit Configs")
    if os.path.exists(main_dir):
        print(f"- \n- Moving the {refs_string}kit configs")

        items_dir = f"{uniform_folder_path}/common/character0/model/character/uniform/team"

        # Create a "team" folder if needed
        os.makedirs(items_dir, exist_ok=True)

        # Move the kit configs to the Uniform cpk folder
        for item in os.listdir(main_dir):
            item_path = os.path.join(main_dir, item)
            target_item_path = os.path.join(items_dir, item)

            # If the target item path exists, remove it
            if os.path.exists(target_item_path):
                shutil.rmtree(target_item_path, onerror=remove_readonly)

            # Move the item to the target directory
            shutil.move(item_path, items_dir)

        # Delete the main 'Kit Configs' folder
        if os.path.exists(main_dir):
            shutil.rmtree(main_dir, onerror=remove_readonly)


    # If there's a Kit Textures folder, move its stuff
    main_dir = os.path.join(extracted_path, "Kit Textures")
    if os.path.exists(main_dir):
        print(f"- \n- Moving the {refs_string}kit textures")

        items_dir = (
            f"{uniform_folder_path}/common/character0/model/character/uniform/texture" if not fox_mode
            else f"{uniform_folder_path}/Asset/model/character/uniform/texture/#windx11"
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
            shutil.rmtree(main_dir, onerror=remove_readonly)


    # If there's a Boots folder, move or pack its stuff
    main_dir = os.path.join(extracted_path, "Boots")
    if os.path.exists(main_dir):

        if not fox_mode:
            print( '-')
            print(f'- Moving the {refs_string}boots')
        else:
            print( '-')
            print(f'- Packing the {refs_string}boots folders')

        models_pack('boots', main_dir, 'boots', faces_folder_path)

    # If there's a Gloves folder, move its stuff
    main_dir = os.path.join(extracted_path, "Gloves")
    if os.path.exists(main_dir):

        if not fox_mode:
            print( '-')
            print(f'- Moving the {refs_string}gloves')
        else:
            print( '-')
            print(f'- Packing the {refs_string}gloves folders')

        models_pack('glove', main_dir, 'glove', faces_folder_path)


    other_message = False

    # If there's a Collars folder, move its stuff
    main_dir = os.path.join(extracted_path, "Collars")
    if os.path.exists(main_dir):

        if not other_message:
            other_message = True

            print( '-')
            print(f'- Moving the other {refs_string}stuff')

        items_folder_path = (
            'common/character0/model/character/uniform/nocloth' if not fox_mode
            else 'Asset/model/character/uniform/nocloth/#Win'
        )

        # Create a "collars" folder if needed
        items_folder_path_full = os.path.join(PATCHES_CONTENTS_PATH, faces_folder_name, items_folder_path)
        if not os.path.exists(items_folder_path_full):
            os.makedirs(items_folder_path_full)

        # Move the collars to the Faces cpk folder
        for item in os.listdir(main_dir):
            shutil.move(os.path.join(main_dir, item), items_folder_path_full)

        # Then delete the main folder
        shutil.rmtree(main_dir, onerror=remove_readonly)


    # If there's a Portraits folder, move its stuff
    main_dir = os.path.join(extracted_path, 'Portraits')
    if os.path.exists(main_dir):

        if not other_message:
            other_message = True

            print( '-')
            print(f'- Moving the other {refs_string}stuff')

        # Create a "player" folder if needed
        items_folder_path_full = os.path.join(PATCHES_CONTENTS_PATH, faces_folder_name, 'common/render/symbol/player')
        if not os.path.exists(items_folder_path_full):
            os.makedirs(items_folder_path_full)

        # Move the portraits to the Faces cpk folder
        for item in os.listdir(main_dir):
            # First delete if it already exists
            if os.path.exists(os.path.join(items_folder_path_full, item)):
                os.remove(os.path.join(items_folder_path_full, item))

            shutil.move(os.path.join(main_dir, item), items_folder_path_full)

        # Then delete the main folder
        shutil.rmtree(main_dir, onerror=remove_readonly)


    # If there's a Logo folder, move its stuff
    main_dir = os.path.join(extracted_path, 'Logo')
    if os.path.exists(main_dir):

        if not other_message:
            other_message = True

            print( '-')
            print(f'- Moving the other {refs_string}stuff')

        # Create a "flag" folder if needed
        items_folder_path_full = os.path.join(PATCHES_CONTENTS_PATH, uniform_folder_name, 'common/render/symbol/flag')
        if not os.path.exists(items_folder_path_full):
            os.makedirs(items_folder_path_full)

        # Move the logos to the Uniform cpk folder
        for item in os.listdir(main_dir):
            # First delete if it already exists
            if os.path.exists(os.path.join(items_folder_path_full, item)):
                os.remove(os.path.join(items_folder_path_full, item))

            shutil.move(os.path.join(main_dir, item), items_folder_path_full)

        # Then delete the main folder
        shutil.rmtree(main_dir, onerror=remove_readonly)


    # Set the common folder path depending on the fox mode setting
    if not fox_mode:
        common_path = 'common/character1/model/character/uniform/common'
    else:
        common_path = 'Asset/model/character/common'

    # If there's a Common folder, move its stuff
    main_dir = os.path.join(extracted_path, 'Common')
    if os.path.exists(main_dir):

        if not other_message:
            other_message = True

            print( '-')
            print(f'- Moving the other {refs_string}stuff')

        # Create a "common" folder if needed
        items_folder_path_full = os.path.join(PATCHES_CONTENTS_PATH, faces_folder_name, common_path)
        if not os.path.exists(items_folder_path_full):
            os.makedirs(items_folder_path_full)

        # Move the team folders to the Faces cpk folder
        for item in os.listdir(main_dir):

            if not fox_mode:

                # If the folder already exists, delete it
                if os.path.exists(os.path.join(items_folder_path_full, item)):
                    shutil.rmtree(os.path.join(items_folder_path_full, item), onerror=remove_readonly)

                # Move the folder
                shutil.move(os.path.join(main_dir, item), items_folder_path_full)

            else:

                # Create a windx11 subfolder for the team
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
        shutil.rmtree(main_dir, onerror=remove_readonly)
