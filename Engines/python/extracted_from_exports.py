import os
import re
import stat
import shutil

from .lib.teamid_get import teamid_get
from .lib.portraits_move import portraits_move
from .lib.export_move import export_move
from .lib.dummy_kit_replace import dummy_kits_replace
from .lib.export_check import export_check
from .lib.utils.zlib_plus import zlib_files_in_folder


def readonlybit_remove_tree(path):
    "Clear the readonly bit on an entire tree"
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWRITE)
        for name in dirs:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWRITE)
        for dir in dirs:
            readonlybit_remove_tree(os.path.join(root, dir))


# Append the contents of a txt file to teamnotes.txt for quick reading
def note_txt_append(team_name, export_destination_path):

    team_name_clean = team_name.replace("/", "").replace("\\", "").upper()
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
    dds_compression = int(os.environ.get('DDS_COMPRESSION', '0'))
    pause_on_error = int(os.environ.get('PAUSE_ON_ERROR', '1'))
    pass_through = int(os.environ.get('PASS_THROUGH', '0'))


    print("- ")
    print("- Extracting and checking the exports")
    print("- ")

    # Define the names of the main folders
    main_source_path = "exports_to_add"
    main_destination_path = "extracted_exports"

    # Create folders just in case
    os.makedirs(main_source_path, exist_ok=True)
    os.makedirs(main_destination_path, exist_ok=True)

    # Define the minimum and maximum team ids
    team_id_min = 701
    team_id_max = 920

    # Reset the notes compilation
    with open("teamnotes.txt", "w") as f:
        f.write("--- 4cc txt notes compilation ---\n")


    for export_name in os.listdir(main_source_path):

        export_source_path = os.path.join(main_source_path, export_name)

        # Check the export type
        if os.path.isdir(export_source_path):
            export_type = "folder"
            export_name_clean = export_name
        elif export_source_path[-4:] == ".zip":
            export_type = "zip"
            export_name_clean = export_name[:-4]
        elif export_source_path[-3:] == ".7z":
            export_type = "7z"
            export_name_clean = export_name[:-3]
        else:
            # If the export is neither a zip, 7z nor a folder, skip it
            print(f"- \"{export_name}\" is unusable - Skipping")
            continue

        export_destination_path = os.path.join(main_destination_path, export_name_clean)

        # Split the words in the export
        export_name_words = re.findall(r"[^\W\_]+", export_name)

        if not export_name_words:
            raise ValueError

        # Get the team name from the first word of the export name
        team_name_raw = export_name_words[0]
        team_name = f"/{team_name_raw.lower()}/"

        # Print team without a new line
        print(f"- {team_name} ", end='')


        # Delete the export destination folder if present
        if os.path.exists(export_destination_path):
            shutil.rmtree(export_destination_path)

        # Extract or copy the export into a new export folder, removing the .db and .ini files
        if not export_type == "folder":
            export_destination_path_temp = export_destination_path + "_temp"
            os.makedirs(export_destination_path_temp, exist_ok=True)

            if export_type == "zip":
                shutil.unpack_archive(export_source_path, export_destination_path_temp, "zip")
            elif export_type == "7z":
                import py7zr
                with py7zr.SevenZipFile(export_source_path, mode='r') as z:
                    z.extractall(export_destination_path_temp)

            shutil.copytree(export_destination_path_temp, export_destination_path, ignore=shutil.ignore_patterns("*.db", "*.ini"))
            shutil.rmtree(export_destination_path_temp)
        else:
            shutil.copytree(export_source_path, export_destination_path, ignore=shutil.ignore_patterns("*.db", "*.ini"))

        # Remove the read-only flag from every item inside the export folder
        readonlybit_remove_tree(export_destination_path)

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

    if dds_compression and not fox_mode:
        # zlib compress all the dds files
        print("- Compressing dds files...")
        print('-')
        zlib_files_in_folder(main_destination_path, "dds")

    print("- Done")
    print('-')

    if not all_in_one:
        if os.path.exists("issues.log"):
            # Warn about there being some issues and about having to open the log
            print('- \033[33m' + 'Warning' + '\033[0m' + ": There were some issues in the exports")
            print("- Please check the issues.log file for a log")
            print('-')
        else:
            print('- No issues were found')
            print('-')

    # Check if the Other folder exists and there are files in it, if there are print a warning
    if os.path.exists("./extracted_exports/Other") and len(os.listdir("./extracted_exports/Other")) > 0:
        print('- \033[33m' + 'Warning' + '\033[0m' + ": There are files in the Other folder")
        print("- Please open it and check its contents")
        print('-')
        if pause_on_error:
            input('Press Enter to continue...')
