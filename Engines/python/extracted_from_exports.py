import os
import re
import shutil
import py7zr

from .lib.teamid_get import teamid_get
from .lib.portraits_move import portraits_move
from .lib.export_move import export_move
from .lib.dummy_kit_replace import dummy_kits_replace
from .lib.export_check import export_check


# Append the contents of a txt file to teamnotes.txt for quick reading
def note_txt_append(team_name, export_destination_path):
    
    team_name_clean = team_name.replace("/", "").replace("\\", "")
    note_path = os.path.join(export_destination_path, f"{team_name_clean} Note.txt")
    teamnotes_name = "teamnotes.txt"
    
    if os.path.exists(note_path):
        
        with open(teamnotes_name, "a") as f2:
            f2.write(f". \n- \n-- {team_name}'s note file: \n- \n")
        with open(note_path, "r", encoding="utf8") as f:
            teamnotes = f.read()
            with open(teamnotes_name, "a", encoding="utf8") as f2:
                f2.write(f"{teamnotes}\n")


def extracted_from_exports():
    
    # Read the necessary parameters
    all_in_one = int(os.environ.get('ALL_IN_ONE', '0'))
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    pass_through = int(os.environ.get('PASS_THROUGH', '0'))
    pause_when_wrong = int(os.environ.get('PAUSE_WHEN_WRONG', '1'))
    
    
    print("- ")
    print("- Extracting and checking the exports")
    print("- ")

    # Define the names of the main folders
    main_source_path = "exports_to_add"
    main_destination_path = "extracted_exports"

    # Create folders just in case
    os.makedirs(main_source_path, exist_ok=True)
    os.makedirs(main_destination_path, exist_ok=True)

    # Clear the flag for writing to file
    os.environ["LOG"] = "0"
    
    # Define the minimum and maximum team ids
    team_id_min = 701
    team_id_max = 920

    # Reset the files
    with open("memelist.txt", "w") as f:
        f.write("--- 4cc aet compiler red - List of problems ---\n")
    with open("teamnotes.txt", "w") as f:
        f.write("--- 4cc txt notes compilation ---\n")


    for export_name in os.listdir(main_source_path):

        # Try to get the first word of the export name
        if re.findall(r"^[^\W\_]+", "".join(re.split(r"^[\W\_]+", export_name)))[0]:
            pass
        else:
            raise ValueError
        
        # Get the team name from the first word of the export name
        team_name_raw = re.findall(r"^[^\W\_]+", "".join(re.split(r"^[\W\_]+", export_name)))[0]
        team_name = f"/{team_name_raw.lower()}/"

        # Print team without a new line
        print(f"- {team_name} ", end='')

        # If the foldername ends with .zip
        if export_name[-4:] == ".zip":
            export_type = "zip"
            export_name_clean = export_name[:-4]
        # If the foldername ends with .7z
        elif export_name[-3:] == ".7z":
            export_type = "7z"
            export_name_clean = export_name[:-3]
        else:
            export_type = "folder"
            export_name_clean = export_name

        export_source_path = os.path.join(main_source_path, export_name)
        export_destination_path = os.path.join(main_destination_path, export_name_clean)
        
        
        # Delete the export destination folder if present
        if os.path.exists(export_destination_path):
            shutil.rmtree(export_destination_path)
        
        # Extract or copy the export into a new export folder
        if not export_type == "folder":
            export_destination_path_temp = export_destination_path + "_temp"
            os.makedirs(export_destination_path_temp, exist_ok=True)
            
            if export_type == "zip":
                shutil.unpack_archive(export_source_path, export_destination_path_temp, "zip")
            elif export_type == "7z":
                with py7zr.SevenZipFile(export_source_path, mode='r') as z:
                    z.extractall(export_destination_path_temp)
                
            shutil.copytree(export_destination_path_temp, export_destination_path, ignore=shutil.ignore_patterns("*.db", "*.ini"))
            shutil.rmtree(export_destination_path_temp)
        else:
            shutil.copytree(export_source_path, export_destination_path, ignore=shutil.ignore_patterns("*.db", "*.ini"))
        
        # Get the team ID
        team_id = teamid_get(export_destination_path, team_name, team_id_min, team_id_max)

        # If the teamID was not found, proceed to the next export
        if not team_id:
            continue
            
        # If the export has a Faces folder
        if os.path.exists(os.path.join(export_destination_path, "Faces")):

            # Move the portraits out of the Faces folder
            export_deleted = portraits_move(export_destination_path, team_id)
        
            # If the export was deleted, proceed to the next export
            if export_deleted:
                continue
        
        # Check the export for all kinds of errors
        if not pass_through:
            export_check(export_destination_path, team_name)
        
        # If the export has a Note.txt file, append it to the teamnotes.txt file
        note_txt_append(team_name, export_destination_path)
        
        # Move the contents of the export to the root of extracted_exports
        export_move(export_destination_path, team_id, team_name)

        # If fox mode is enabled and the team has a common folder replace the dummy textures with the kit 1 textures
        if fox_mode and os.path.exists(os.path.join(os.path.dirname(export_destination_path), "Common", team_id)):
            dummy_kits_replace(team_id, team_name)

        # Delete the now empty export folder
        shutil.rmtree(export_destination_path)

        print("- ")

    print("- Done")
    print('-')

    log = int(os.environ.get('LOG', '0'))

    if not all_in_one:
        if log:
            # Warn about there being some issues and about having to open memelist.txt
            print("- Warning: There were some issues in the exports")
            print("- Please check the memelist.txt file for a log")
            print('-')
        else:
            print('- No issues were found')
            print('-')
        

    # Check if the Other folder exists and there are files in it, if there are print a warning
    if os.path.exists("./extracted_exports/Other") and len(os.listdir("./extracted_exports/Other")) > 0:
        print("- Warning: There are files in the Other folder")
        print("- Please open it and check its contents")
        print('-')
        if pause_when_wrong:
            input('Press Enter to continue...')

