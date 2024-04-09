## Moves the contents of the export to the root of extracted_exports
import os
import re
import shutil

from .utils.ftex import ddsToFtex
from .utils.zlib_plus import unzlib_file
from .mtl_id_change import mtl_id_change
from .fmdl_id_change import transfer


# Handles dds to ftex conversion of an entire folder
def ftex_from_dds_multi(folder_path):
    for dds_file in [f for f in os.listdir(folder_path) if f.endswith('.dds')]:
        
        dds_path = os.path.join(folder_path, dds_file)
        ftex_path = os.path.splitext(dds_path)[0] + '.ftex'
        
        ddsToFtex(dds_path, ftex_path, None)
        os.remove(dds_path)


# Replaces the dummy team ID with the actual one in any kit-dependent textures found in the folder
def textures_id_change(subfolder_path, team_id):
    for texture_file in [f for f in os.listdir(subfolder_path) if f.endswith(('.dds', '.ftex'))]:
        
        texture_path = os.path.join(subfolder_path, texture_file)
        
        # Look for u0XXXp and replace it with the actual team ID
        texture_path_new = re.sub(r'u0([a-zA-Z0-9]){3}p', 'u0'+team_id+'p', texture_path)
        
        if texture_path_new == texture_path:
            continue
        
        if os.path.exists(texture_path_new):
            os.remove(texture_path_new)
        os.rename(texture_path, texture_path_new)


def export_move(exportfolder_path, team_id, team_name):
    
    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    fox_19 = (int(os.environ.get('PES_VERSION', '19')) >= 19)
    fox_21 = (int(os.environ.get('PES_VERSION', '19')) >= 21)

    # The main folder path is the parent of the export folder
    mainfolder_path = os.path.dirname(exportfolder_path)
    
    # Prepare a clean version of the team name without slashes
    team_name_clean = team_name.replace('/', '').replace('\\', '')
    
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
        
        # If the folder is a known type
        if team_itemfolder_name.lower() in ["faces", "kit configs", "kit textures", "logo", "portraits", "boots", "gloves", "common", "other"]:

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
            
            # For each subfolder
            for subfolder_name in [subfolder for subfolder in os.listdir(team_itemfolder_path)
                                   if os.path.isdir(os.path.join(team_itemfolder_path, subfolder))]:
                subfolder_path = os.path.join(team_itemfolder_path, subfolder_name)

                # Replace the dummy team ID with the actual one
                subfolder_id_withname = team_id + subfolder_name[3:]
                subfolder_id = subfolder_id_withname[:5]
                
                if fox_mode:
                    # Change the texture IDs inside each fmdl file
                    for fmdl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".fmdl")]:
                        transfer(os.path.join(subfolder_path, fmdl_file), subfolder_id, team_id)
                    
                    # Convert any dds textures to ftex if needed
                    ftex_from_dds_multi(subfolder_path)

                else:
                    # Change the texture IDs inside each mtl file
                    for mtl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".mtl")]:
                        mtl_id_change(os.path.join(subfolder_path, mtl_file), team_id)
                
                # Replace the dummy team ID with the actual one in any kit-dependent textures found
                textures_id_change(subfolder_path, team_id)

                # Replace the dummy team ID with the actual one
                os.rename(subfolder_path, os.path.join(team_itemfolder_path, subfolder_id_withname))
                    
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

            # Prepare the base texture filename
            texname = "0" + team_id

            # For every file
            for file_name in [f for f in os.listdir(team_itemfolder_path) if f.endswith(".bin")]:
                file_path = os.path.join(team_itemfolder_path, file_name)

                # Unzlib it if needed
                unzlib_file(file_path)
                
                # Edit the texture names inside the config file so that they point to the proper textures
                texname_bytes = texname.encode('utf-8')  # Convert to bytes
                with open(file_path, 'rb+') as file:
                    for line in range(5):
                        position = 40 + line * 16
                        file.seek(position)
                        char = file.read(1)
                        if char == b'u':
                            file.write(texname_bytes)  # Overwrite with the texture name
                
                # Replace the dummy team ID in the filename with the actual one
                file_name_new = team_id + file_name[3:]
                file_path_new = os.path.join(team_itemfolder_path, file_name_new)
                os.rename(file_path, file_path_new)

                # Move the file to the team folder inside the main folder
                shutil.move(file_path_new, main_itemfolder_team_path)

        # Kit Textures folder
        if team_itemfolder_name.lower() == "kit textures":
            
            # Convert any dds textures to ftex if needed
            if fox_mode:
                ftex_from_dds_multi(team_itemfolder_path)
            
            # Set the texture file extension to ftex or dds
            file_ext = 'ftex' if fox_mode else 'dds'

            # For every file
            for file_name in [f for f in os.listdir(team_itemfolder_path) if f.endswith(f".{file_ext}")]:
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
            
            # For each subfolder
            for subfolder_name in [subfolder for subfolder in os.listdir(team_itemfolder_path)
                                   if os.path.isdir(os.path.join(team_itemfolder_path, subfolder))]:
                subfolder_path = os.path.join(team_itemfolder_path, subfolder_name)

                # Get the ID
                subfolder_id = subfolder_name[:5]
                
                if fox_mode:
                    # Change the texture IDs inside each fmdl file
                    for fmdl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".fmdl")]:
                        transfer(os.path.join(subfolder_path, fmdl_file), subfolder_id, team_id)
                    
                    # Convert any dds textures to ftex if needed
                    ftex_from_dds_multi(subfolder_path)
                
                else:
                    # Change the texture IDs inside each mtl file
                    for mtl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".mtl")]:
                        mtl_id_change(os.path.join(subfolder_path, mtl_file), team_id)
                
                # Replace the dummy team ID with the actual one in any kit-dependent textures found
                textures_id_change(subfolder_path, team_id)
                
                # Delete the destination folder if already present
                subfolder_destination_path = os.path.join(main_itemfolder_path, subfolder_name)
                if os.path.exists(subfolder_destination_path):
                    shutil.rmtree(subfolder_destination_path)
                    
                # Move the folder to the main folder
                shutil.move(subfolder_path, main_itemfolder_path)

        # Gloves folder
        if team_itemfolder_name.lower() == "gloves":
            
            # For each subfolder
            for subfolder_name in [subfolder for subfolder in os.listdir(team_itemfolder_path)
                                   if os.path.isdir(os.path.join(team_itemfolder_path, subfolder))]:
                subfolder_path = os.path.join(team_itemfolder_path, subfolder_name)

                # Get the ID
                subfolder_id = subfolder_name[:5]
                
                if fox_mode:
                    # Change the texture IDs inside each fmdl file
                    for fmdl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".fmdl")]:
                        transfer(os.path.join(subfolder_path, fmdl_file), subfolder_id, team_id)
                    
                    # Convert any dds textures to ftex if needed
                    ftex_from_dds_multi(subfolder_path)
                
                else:
                    # Change the texture IDs inside each mtl file
                    for mtl_file in [f for f in os.listdir(subfolder_path) if f.endswith(".mtl")]:
                        mtl_id_change(os.path.join(subfolder_path, mtl_file), team_id)
                
                # Replace the dummy team ID with the actual one in any kit-dependent textures found
                textures_id_change(subfolder_path, team_id)
                
                # Delete the destination folder if already present
                subfolder_destination_path = os.path.join(main_itemfolder_path, subfolder_name)
                if os.path.exists(subfolder_destination_path):
                    shutil.rmtree(subfolder_destination_path)
                
                # Move the folder to the main folder
                shutil.move(os.path.join(team_itemfolder_path, subfolder_name), main_itemfolder_path)
        
        # Collars folder
        if team_itemfolder_name.lower() == "collars":
            
            # For each file
            for file_name in os.listdir(os.path.join(team_itemfolder_path, file_name)):

                # Delete the destination file if already present
                file_destination_path = os.path.join(main_itemfolder_path, file_name)
                if os.path.exists(file_destination_path):
                    os.remove(file_destination_path)

                # Move the file to the main folder
                os.replace(os.path.join(team_itemfolder_path, file_name), main_itemfolder_path)

        # Common folder
        if team_itemfolder_name.lower() == "common":
            
            # First check that it isn't empty
            if any(os.listdir(team_itemfolder_path)):
                
                # Delete the team folder in the main folder if already present
                if os.path.exists(main_itemfolder_team_path):
                    shutil.rmtree(main_itemfolder_team_path)

                # Create a folder with the team ID in the main folder
                os.makedirs(main_itemfolder_team_path)

                # Convert any dds textures to ftex if needed
                if fox_mode:
                    ftex_from_dds_multi(team_itemfolder_path)
                
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


