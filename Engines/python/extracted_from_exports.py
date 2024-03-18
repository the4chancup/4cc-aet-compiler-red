import os
import sys
import subprocess
import shutil
import importlib
import subprocess

from lib.teamid_get import teamid_get
from lib.portraits_move import portraits_move
from lib.export_move import export_move
from lib.dummy_kit_replace import dummy_kits_replace
from lib.export_check import export_check


# Read the necessary parameters
all_in_one = int(os.environ.get('ALL_IN_ONE', '0'))
fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
pass_through = int(os.environ.get('PASS_THROUGH', '0'))
pause_when_wrong = int(os.environ.get('PAUSE_WHEN_WRONG', '1'))


# Check if py7zr is installed
def py7zr_check():
    try:
        importlib.import_module('py7zr')
    except ImportError:
        print("- py7zr library not found.")
        print("- This library is needed to extract the 7z files.")
        print("- Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "py7zr"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Warn about the program having to be started again, then exit after pressing Enter
        input("- ")
        input("- Library installed. Please run this program again.")
        input("- ")
        input("Press Enter to exit...")
        exit()


def extracted_from_exports():
    
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
    memelist = ""

    # Reset the files
    with open("memelist.txt", "w") as f:
        f.write("--- 4cc aet compiler red - List of problems ---\n")
    with open("teamnotes.txt", "w") as f:
        f.write("--- 4cc txt notes compilation ---\n")


    for export_name in os.listdir(main_source_path):

        export_type_zip = False
        export_type_7z = False

        team_raw = export_name.split(' ')[0]
        team_name = f"/{team_raw.lower()}/"

        # Print team without a new line
        print(f"- {team_name} ", end='')

        # If the foldername ends with .zip
        if export_name[-4:] == ".zip":
            export_type_zip = True
            export_name_clean = export_name[:-4]
        # If the foldername ends with .7z
        elif export_name[-3:] == ".7z":
            export_type_7z = True
            export_name_clean = export_name[:-3]
        else:
            export_name_clean = export_name

        export_source_path = os.path.join(main_source_path, export_name)
        export_destination_path = os.path.join(main_destination_path, export_name_clean)
        
        
        # Delete the export destination folder if present
        if os.path.exists(export_destination_path):
            shutil.rmtree(export_destination_path)
        
        # Extract or copy the export into a new export folder
        if export_type_zip:
            os.makedirs(export_destination_path)
            shutil.unpack_archive(export_source_path, export_destination_path, "zip", ignore=shutil.ignore_patterns("*.db", "*.ini"))
        elif export_type_7z:
            py7zr_check()
            import py7zr
            os.makedirs(export_destination_path)
            with py7zr.SevenZipFile(export_source_path, mode='r') as z:
                z.extractall(path=export_destination_path, wildcard="* !*.db !*.ini")
        else:
            shutil.copytree(export_source_path, export_destination_path, ignore=shutil.ignore_patterns("*.db", "*.ini"))
        
        # Get the team ID
        team_id = teamid_get(export_destination_path, team_name)

        # If the teamID was found
        if team_id:

            # If the export has a Faces folder
            if os.path.exists(os.path.join(export_destination_path, "Faces")):

                # Move the portraits out of the Faces folder
                portraits_move(export_destination_path, team_id)

            # Check the export for all kinds of errors
            if not pass_through:
                export_check(export_destination_path, team_name)
            
            # If the export has a Note.txt file
            note_path = os.path.join(export_destination_path, f"{team_raw} Note.txt")
            if os.path.exists(note_path):
                # Append the contents of the txt file to teamnotes.txt for quick reading
                with open("teamnotes.txt", "a") as f2:
                    f2.write(f". \n- \n-- {team_name}'s note file: \n- \n")
                with open(note_path, "r") as f:
                    teamnotes = f.read()
                    with open("teamnotes.txt", "a") as f2:
                        f2.write(f"{teamnotes}\n")
            
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
            print("- Warning: There were some issues in the exports.")
            print("- Please check the memelist.txt file for a log.")
            print('-')
        else:
            print('- No issues were found.')
            print('-')
        

    # Check if the Other folder exists and there are files in it, if there are print a warning
    if os.path.exists("./extracted_exports/Other") and len(os.listdir("./extracted_exports/Other")) > 0:
        print("- Warning: There are files in the Other folder.")
        print("- Please open it and check its contents.")
        print('-')
        if pause_when_wrong:
            input('Press Enter to continue...')
            