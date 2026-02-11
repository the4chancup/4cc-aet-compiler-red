import os
import time
import shutil

from .fmdl_id_change import fmdl_id_change
from .xml_editing import xml_create
from .xml_editing import xml_process
from .utils.file_management import file_critical_check
from .utils.texture_conversion import textures_convert
from .utils.zlib_plus import unzlib_file
from .utils.name_editing import (
    model_names_fix,
    filenames_id_replace,
    fix_mtl_paths,
    txt_id_change,
)
from .utils.FILE_INFO import (
    TEMPLATE_FOLDER_PATH,
    KIT_MASK_NAME,
    FACE_DIFF_BIN_NAME,
)


def kit_masks_check(team_itemfolder_path, file_ext):

    kit_texture_main_list = []

    # Prepare a list of textures
    file_name_list = [f for f in os.listdir(team_itemfolder_path) if f.endswith(f".{file_ext}")]

    for file_name in file_name_list:

        # If the name is eleven chars long (u0XXXxX.dds), add the texture to the list of main textures
        if len(file_name) == 11:
            kit_texture_main_list.append(file_name)

    for kit_texture_main in kit_texture_main_list:

        # Check if there is a corresponding "_mask" texture
        kit_texture_mask = f"{kit_texture_main[:-4]}_mask.{file_ext}"

        if kit_texture_mask not in file_name_list:
            # Copy the default kit mask texture from the templates folder
            KIT_MASK_TEMPLATE_PATH = os.path.join(TEMPLATE_FOLDER_PATH, KIT_MASK_NAME)
            kit_texture_mask_destination = os.path.join(team_itemfolder_path, kit_texture_mask)
            file_critical_check(KIT_MASK_TEMPLATE_PATH)
            shutil.copy(KIT_MASK_TEMPLATE_PATH, kit_texture_mask_destination)


def export_move(exportfolder_path, team_id, team_name):
    '''Move the contents of the export to the root of the "extracted" folder'''

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    fox_19 = (int(os.environ.get('PES_VERSION', '19')) >= 19)
    fox_21 = (int(os.environ.get('PES_VERSION', '19')) >= 21)
    pes_15 = (int(os.environ.get('PES_VERSION', '19')) == 15)

    # The main folder path is the parent of the export folder
    mainfolder_path = os.path.dirname(exportfolder_path)

    # Prepare a clean version of the team name without slashes
    team_name_clean = team_name.replace("/", "").replace("\\", "").upper()

    itemfolder_unknown_pres = False

    # Move all the files which are not in a folder
    for item in os.listdir(exportfolder_path):
        item_path = os.path.join(exportfolder_path, item)
        if os.path.isfile(item_path):
            # Delete the destination file if already present
            destination_path = os.path.join(mainfolder_path, item)
            if os.path.exists(destination_path):
                os.remove(destination_path)
            shutil.move(item_path, mainfolder_path)

    # For each item folder
    for team_itemfolder_name in os.listdir(exportfolder_path):

        itemfolder_name_known_list = [
            "faces",
            "kit configs",
            "kit textures",
            "logo",
            "portraits",
            "boots",
            "gloves",
            "collars",
            "common",
            "other"
        ]
        # If the folder is a known type
        if team_itemfolder_name.lower() in itemfolder_name_known_list:

            team_itemfolder_path = os.path.join(exportfolder_path, team_itemfolder_name)
            main_itemfolder_path = os.path.join(mainfolder_path, team_itemfolder_name)
            main_itemfolder_team_path = os.path.join(main_itemfolder_path, team_id)

            # Create the main folder if not present
            if not os.path.exists(main_itemfolder_path):
                os.makedirs(main_itemfolder_path)

        # If the folder is out of the AET specifics
        else:

            # Look for it later to avoid the Other folder getting reset
            itemfolder_unknown_pres = True


        # Faces folder
        if team_itemfolder_name.lower() == "faces":

            if fox_mode:
                FACE_DIFF_BIN_TEMPLATE_PATH = os.path.join(TEMPLATE_FOLDER_PATH, FACE_DIFF_BIN_NAME)
                file_critical_check(FACE_DIFF_BIN_TEMPLATE_PATH)

            # Prepare a list of subfolders
            subfolder_list = [subfolder for subfolder in os.listdir(team_itemfolder_path) if os.path.isdir(os.path.join(team_itemfolder_path, subfolder))]

            # For each subfolder
            for subfolder_name in subfolder_list:
                subfolder_path = os.path.join(team_itemfolder_path, subfolder_name)

                # Replace the dummy team ID with the actual one
                if team_name == "/refs/":
                    # For referees, face IDs are in the format "refereeXXX" where XXX is the ref number
                    subfolder_id_withname = subfolder_name
                    subfolder_id = subfolder_id_withname[:10]  # "referee001"
                else:
                    # Normal team face handling
                    subfolder_id_withname = team_id + subfolder_name[3:]
                    subfolder_id = subfolder_id_withname[:5]

                if fox_mode:
                    # Change the texture IDs inside each fmdl file
                    for fmdl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".fmdl")]:
                        fmdl_id_change(os.path.join(subfolder_path, fmdl_file), subfolder_id, team_id)

                    # If the face_diff.bin doesn't exist, copy the template one
                    face_diff_path = os.path.join(subfolder_path, FACE_DIFF_BIN_NAME)
                    if not os.path.exists(face_diff_path):
                        shutil.copyfile(FACE_DIFF_BIN_TEMPLATE_PATH, face_diff_path)

                else:
                    # Change the texture IDs inside each mtl file
                    for mtl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".mtl")]:
                        txt_id_change(os.path.join(subfolder_path, mtl_file), team_id)

                    object_type = "face"
                    xml_path = os.path.join(subfolder_path, f"{object_type}.xml")
                    if not os.path.exists(xml_path):
                        # Create the xml file
                        xml_create(subfolder_path, object_type)
                    # Process the xml file
                    xml_process(xml_path, team_id)

                # Convert unsupported textures
                textures_convert(subfolder_path, fox_mode, fox_19)

                # Replace the dummy team ID with the actual one in any files found
                filenames_id_replace(subfolder_path, team_id)

                # Replace the dummy team ID with the actual one
                subfolder_path_withname = os.path.join(team_itemfolder_path, subfolder_id_withname)
                if subfolder_path_withname != subfolder_path:
                    try:
                        os.rename(subfolder_path, subfolder_path_withname)
                    except OSError:
                        time.sleep(1)
                        os.rename(subfolder_path, subfolder_path_withname)

                # Delete the destination folder if already present
                subfolder_destination_path = os.path.join(main_itemfolder_path, subfolder_id_withname)
                if os.path.exists(subfolder_destination_path):
                    shutil.rmtree(subfolder_destination_path)

                # Move the folder to the main folder
                shutil.move(os.path.join(team_itemfolder_path, subfolder_id_withname), main_itemfolder_path)

        # Kit Configs folder
        if team_itemfolder_name.lower() == "kit configs":

            # Delete the team folder in the main folder if already present
            if os.path.exists(main_itemfolder_team_path):
                shutil.rmtree(main_itemfolder_team_path)

            # Create a folder with the team ID in the main folder
            os.makedirs(main_itemfolder_team_path)

            # Prepare the team ID for the texture filenames
            team_id_full = "0" + team_id
            team_id_full_bytes = team_id_full.encode('utf-8')

            def change_pattern(file_path):

                # Check the last three bits of byte 0x24 (shirt pattern)
                with open(file_path, 'rb+') as file:
                    file.seek(0x24)
                    val_byte = file.read(1)
                    val_int = ord(val_byte)

                    if val_int & 0xE0 == 0xC0:
                        # Change 6 to 5
                        new_pattern = 0xA0
                    else:
                        return

                    new_int = val_int & 0x1F | new_pattern
                    new_byte = bytes([new_int])
                    file.seek(0x24)
                    file.write(new_byte)

            # For every file
            for file_name in [f for f in os.listdir(team_itemfolder_path) if f.endswith(".bin")]:
                file_path = os.path.join(team_itemfolder_path, file_name)

                # Unzlib it if needed
                unzlib_file(file_path)

                # Edit the texture filenames inside the config file
                with open(file_path, 'rb+') as file:
                    for line in range(5):
                        position = 40 + line * 16
                        file.seek(position)
                        char = file.read(1)
                        if char == b'u':
                            # Update the team ID in the texture filename
                            file.write(team_id_full_bytes)

                if pes_15:
                    change_pattern(file_path)

                # Replace the dummy team ID in the filename with the actual one
                file_name_new = team_id + file_name[3:]
                file_path_new = os.path.join(team_itemfolder_path, file_name_new)
                os.rename(file_path, file_path_new)

                # Delete the destination file if already present
                file_destination_path = os.path.join(main_itemfolder_team_path, file_name_new)
                if os.path.exists(file_destination_path):
                    os.remove(file_destination_path)

                # Move the file to the team folder inside the main folder
                shutil.move(file_path_new, main_itemfolder_team_path)

        # Kit Textures folder
        if team_itemfolder_name.lower() == "kit textures":

            # Set the texture file extension to ftex or dds
            file_ext = 'ftex' if fox_mode else 'dds'

            if not fox_mode:
                # Add any missing kit masks
                kit_masks_check(team_itemfolder_path, file_ext)

            # Convert unsupported textures
            textures_convert(team_itemfolder_path, fox_mode, fox_19)

            # Prepare a list of textures
            file_name_list = [f for f in os.listdir(team_itemfolder_path) if f.endswith(f".{file_ext}")]

            # For every file
            for file_name in file_name_list:
                file_path = os.path.join(team_itemfolder_path, file_name)

                # Replace the dummy team ID with the actual one
                file_name_new = f"u0{team_id}{file_name[5:]}"
                file_path_new = f'{team_itemfolder_path}/{file_name_new}'
                os.rename(file_path, file_path_new)

                # Delete the destination file if already present
                file_destination_path = os.path.join(main_itemfolder_path, file_name_new)
                if os.path.exists(file_destination_path):
                    os.remove(file_destination_path)

                # Move the file to the main folder
                shutil.move(file_path_new, main_itemfolder_path)

        # Logo folder
        if team_itemfolder_name.lower() == "logo":

            # For every file
            for file_name in os.listdir(team_itemfolder_path):
                file_path = os.path.join(team_itemfolder_path, file_name)

                # Replace the dummy team ID with the actual one
                if fox_21:
                    file_name_new = f"e_000{team_id}{file_name[11:]}"
                else:
                    file_name_new = f"emblem_0{team_id}{file_name[11:]}"

                file_path_new = f'{team_itemfolder_path}/{file_name_new}'
                os.rename(file_path, file_path_new)

                # Delete the destination file if already present
                file_destination_path = os.path.join(main_itemfolder_path, file_name_new)
                if os.path.exists(file_destination_path):
                    os.remove(file_destination_path)

                # Move the file to the main folder
                shutil.move(file_path_new, main_itemfolder_path)

        # Portraits folder
        if team_itemfolder_name.lower() == "portraits":

            # Convert unsupported textures
            # Fox mode is forced to False because the portraits need to stay in DDS format
            textures_convert(team_itemfolder_path, False, fox_19)

            # For every file
            for file_name in os.listdir(team_itemfolder_path):
                file_path = os.path.join(team_itemfolder_path, file_name)

                # Replace the dummy team ID with the actual one
                if file_name.startswith("player_"):
                    player_id = file_name[-6:-4]
                else:
                    player_id = file_name[3:5]

                if fox_19:
                    file_name_new = f"{team_id}{player_id}.dds"
                else:
                    file_name_new = f"player_{team_id}{player_id}.dds"

                file_path_new = f'{team_itemfolder_path}/{file_name_new}'
                os.rename(file_path, file_path_new)

                # Delete the destination file if already present
                file_destination_path = os.path.join(main_itemfolder_path, file_name_new)
                if os.path.exists(file_destination_path):
                    os.remove(file_destination_path)

                # Move the file to the main folder
                shutil.move(file_path_new, main_itemfolder_path)

        # Boots folder
        if team_itemfolder_name.lower() == "boots":

            # Prepare a list of subfolders
            subfolder_list = [subfolder for subfolder in os.listdir(team_itemfolder_path) if os.path.isdir(os.path.join(team_itemfolder_path, subfolder))]

            # For each subfolder
            for subfolder_name in subfolder_list:
                subfolder_path = os.path.join(team_itemfolder_path, subfolder_name)

                # Get the ID
                subfolder_id = subfolder_name[:5]

                if fox_mode:
                    # Change the texture IDs inside each fmdl file
                    for fmdl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".fmdl")]:
                        fmdl_id_change(os.path.join(subfolder_path, fmdl_file), subfolder_id, team_id)

                else:
                    # Change the texture IDs inside each mtl file
                    for mtl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".mtl")]:
                        txt_id_change(os.path.join(subfolder_path, mtl_file), team_id)

                # Convert unsupported textures
                textures_convert(subfolder_path, fox_mode, fox_19)

                # Replace the dummy team ID with the actual one in any files found
                filenames_id_replace(subfolder_path, team_id)

                # Delete the destination folder if already present
                subfolder_destination_path = os.path.join(main_itemfolder_path, subfolder_name)
                if os.path.exists(subfolder_destination_path):
                    shutil.rmtree(subfolder_destination_path)

                # Move the folder to the main folder
                shutil.move(subfolder_path, main_itemfolder_path)

        # Gloves folder
        if team_itemfolder_name.lower() == "gloves":

            # Prepare a list of subfolders
            subfolder_list = [subfolder for subfolder in os.listdir(team_itemfolder_path) if os.path.isdir(os.path.join(team_itemfolder_path, subfolder))]

            # For each subfolder
            for subfolder_name in subfolder_list:
                subfolder_path = os.path.join(team_itemfolder_path, subfolder_name)

                # Get the ID
                subfolder_id = subfolder_name[:5]

                if fox_mode:
                    # Change the texture IDs inside each fmdl file
                    for fmdl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".fmdl")]:
                        fmdl_id_change(os.path.join(subfolder_path, fmdl_file), subfolder_id, team_id)

                else:
                    # Change the texture IDs inside each mtl file
                    for mtl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".mtl")]:
                        txt_id_change(os.path.join(subfolder_path, mtl_file), team_id)

                    object_type = "glove"
                    xml_path = os.path.join(subfolder_path, f"{object_type}.xml")
                    if not os.path.exists(xml_path):
                        # Create the xml file
                        xml_create(subfolder_path, object_type)
                    # Process the xml file
                    xml_process(xml_path, team_id)

                # Convert unsupported textures
                textures_convert(subfolder_path, fox_mode, fox_19)

                # Replace the dummy team ID with the actual one in any files found
                filenames_id_replace(subfolder_path, team_id)

                # Delete the destination folder if already present
                subfolder_destination_path = os.path.join(main_itemfolder_path, subfolder_name)
                if os.path.exists(subfolder_destination_path):
                    shutil.rmtree(subfolder_destination_path)

                # Move the folder to the main folder
                shutil.move(os.path.join(team_itemfolder_path, subfolder_name), main_itemfolder_path)

        # Collars folder
        if team_itemfolder_name.lower() == "collars":

            # For each file
            for file_name in os.listdir(team_itemfolder_path):
                file_path = os.path.join(team_itemfolder_path, file_name)

                # Delete the destination file if already present
                file_destination_path = os.path.join(main_itemfolder_path, file_name)
                if os.path.exists(file_destination_path):
                    os.remove(file_destination_path)

                # Move the file to the main folder
                os.replace(file_path, main_itemfolder_path)

        # Common folder
        if team_itemfolder_name.lower() == "common":

            # First check that it isn't empty
            if any(os.listdir(team_itemfolder_path)):

                # Delete the team folder in the main folder if already present
                if os.path.exists(main_itemfolder_team_path):
                    shutil.rmtree(main_itemfolder_team_path)

                # Create a folder with the team ID in the main folder
                os.makedirs(main_itemfolder_team_path)

                if not fox_mode:
                    for mtl_file in [f for f in os.listdir(team_itemfolder_path) if f.endswith(".mtl")]:
                        mtl_path = os.path.join(team_itemfolder_path, mtl_file)

                        # Change the texture IDs inside each mtl file
                        txt_id_change(mtl_path, team_id)

                        # Replace any relative paths with absolute ones
                        fix_mtl_paths(mtl_path, team_id)

                # Convert unsupported textures
                textures_convert(team_itemfolder_path, fox_mode, fox_19)

                # Replace the dummy team ID with the actual one in any files found
                filenames_id_replace(team_itemfolder_path, team_id)

                # Add oral_ and _win32 to any lacking model file names found in the folder
                model_names_fix(team_itemfolder_path)

                # Move everything to the team folder inside the main folder
                for file in os.listdir(team_itemfolder_path):
                    shutil.move(os.path.join(team_itemfolder_path, file), main_itemfolder_team_path)

        # Other folder
        if team_itemfolder_name.lower() == "other":

            # First check that it isn't empty
            if any(os.listdir(team_itemfolder_path)):

                otherfolder_team_path = os.path.join(main_itemfolder_path, f"{team_id} - {team_name_clean}")

                # Make a team folder with the team ID and name after deleting it if already present
                if os.path.exists(otherfolder_team_path):
                    shutil.rmtree(otherfolder_team_path)
                os.makedirs(otherfolder_team_path)

                # Move everything to that folder
                for file in os.listdir(team_itemfolder_path):
                    shutil.move(os.path.join(team_itemfolder_path, file), otherfolder_team_path)


    # If there were any unknown folders
    if itemfolder_unknown_pres:

        # Look for them
        for team_itemfolder_name in os.listdir(exportfolder_path):

            if team_itemfolder_name.lower() not in ["faces", "kit configs", "kit textures", "logo", "portraits", "boots", "gloves", "common", "other"]:

                # First check that it isn't empty
                team_itemfolder_path = os.path.join(exportfolder_path, team_itemfolder_name)

                if any(os.scandir(team_itemfolder_path)):

                    # Make a team folder in Other for the team
                    otherfolder_team_path = os.path.join(exportfolder_path, "Other", f"{team_id} - {team_name_clean}")
                    os.makedirs(otherfolder_team_path, exist_ok=True)

                    # Delete the subfolder if already present
                    subfolder_destination_path = os.path.join(otherfolder_team_path, team_itemfolder_name)
                    if os.path.exists(subfolder_destination_path):
                        os.rmdir(subfolder_destination_path)

                    # Move it
                    shutil.move(team_itemfolder_path, otherfolder_team_path)
