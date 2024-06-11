import os
import re
import py7zr
import shutil

from .lib.team_id_get import team_id_get
from .lib.portraits_move import portraits_move
from .lib.export_move import export_move
from .lib.dummy_kit_replace import dummy_kits_replace
from .lib.export_check import export_check
from .lib.utils.zlib_plus import zlib_files_in_folder
from .lib.utils.pausing import pause
from .lib.utils import COLORS
from .lib.utils.app_tools import log_presence_warn
from .lib.utils.FILE_INFO import (
    EXPORTS_TO_ADD_PATH,
    EXTRACTED_PATH,
    TEAMNOTES_PATH,
)


def readonlybit_remove_tree(path):
    "Clear the readonly bit on an entire tree"
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, 0o600)
        for name in dirs:
            filename = os.path.join(root, name)
            os.chmod(filename, 0o700)
        for dir in dirs:
            readonlybit_remove_tree(os.path.join(root, dir))


# Append the contents of a txt file to teamnotes.txt for quick reading
def note_txt_append(team_name, export_destination_path):

    team_name_clean = team_name.replace("/", "").replace("\\", "").upper()
    note_path = os.path.join(export_destination_path, f"{team_name_clean} Note.txt")

    if not os.path.exists(note_path):
        return

    with open(TEAMNOTES_PATH, "a") as f2:
        f2.write(f". \n- \n-- {team_name}'s note file: \n- \n")
    with open(note_path, "r", encoding="utf8") as f:
        teamnotes = f.read()
        with open(TEAMNOTES_PATH, "a", encoding="utf8") as f2:
            f2.write(f"{teamnotes}\n")


def extracted_from_exports():

    # Read the necessary parameters
    all_in_one = int(os.environ.get('ALL_IN_ONE', '0'))
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    dds_compression = int(os.environ.get('DDS_COMPRESSION', '0'))
    pause_on_error = int(os.environ.get('PAUSE_ON_ERROR', '1'))
    pass_through = int(os.environ.get('PASS_THROUGH', '0'))


    print("-")
    print("- Extracting and checking the exports")
    print("-")

    # Define the names of the main folders
    main_source_path = EXPORTS_TO_ADD_PATH
    main_destination_path = EXTRACTED_PATH

    # Create folders as needed
    os.makedirs(main_source_path, exist_ok=True)

    if os.path.exists(main_destination_path):
        shutil.rmtree(main_destination_path)
    os.makedirs(main_destination_path)

    # Define the minimum and maximum team ids
    team_id_min = 701
    team_id_max = 920

    # Reset the notes compilation
    with open(TEAMNOTES_PATH, "w") as f:
        f.write("--- 4cc txt notes compilation ---\n")

    EXPORT_FILE_TYPES_LIST = [".zip", ".7z"]

    for export_name in os.listdir(main_source_path):

        export_source_path = os.path.join(main_source_path, export_name)

        # Check the export type
        if os.path.isdir(export_source_path):
            export_type = "folder"
            export_name_clean = export_name
        else:
            export_name_clean, export_type = os.path.splitext(export_name)

            if export_type not in EXPORT_FILE_TYPES_LIST:
                # If the export is neither a folder nor an accepted type, skip it
                print(f"- \"{export_name}\" is unusable - Skipping")
                continue

        export_destination_path = os.path.join(main_destination_path, export_name_clean)

        # Split the words in the export
        export_name_words = re.findall(r"[^.\s\-\+\_]+", export_name)

        if not export_name_words:
            raise ValueError

        # Get the team name from the first word of the export name
        team_name_folder_raw = export_name_words[0]
        team_name_folder = f"/{team_name_folder_raw.lower()}/"

        # Print team without a new line
        print(f"- {team_name_folder} ", end='', flush=True)


        # Delete the export destination folder if present
        if os.path.exists(export_destination_path):
            shutil.rmtree(export_destination_path)

        # Extract or copy the export into a new export folder, removing the .db and .ini files
        if not export_type == "folder":
            export_destination_path_temp = export_destination_path + "_temp"
            os.makedirs(export_destination_path_temp, exist_ok=True)

            if export_type == ".zip":
                shutil.unpack_archive(export_source_path, export_destination_path_temp, "zip")
            elif export_type == ".7z":
                with py7zr.SevenZipFile(export_source_path, mode='r') as z:
                    z.extractall(export_destination_path_temp)

            shutil.copytree(export_destination_path_temp, export_destination_path, ignore=shutil.ignore_patterns("*.db", "*.ini"))
            shutil.rmtree(export_destination_path_temp)
        else:
            shutil.copytree(export_source_path, export_destination_path, ignore=shutil.ignore_patterns("*.db", "*.ini"))

        # Remove the read-only flag from every item inside the export folder
        readonlybit_remove_tree(export_destination_path)

        # Get the team ID and real name
        team_id, team_name = team_id_get(export_destination_path, team_name_folder, team_id_min, team_id_max)

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
            export_check(export_destination_path, team_name, team_id)

        # If the export has a Note.txt file, append it to the teamnotes.txt file
        note_txt_append(team_name, export_destination_path)

        # Move the contents of the export to the root of "extracted"
        export_move(export_destination_path, team_id, team_name)

        # If fox mode is enabled and the team has a common folder replace the dummy textures with the kit 1 textures
        if fox_mode and os.path.exists(os.path.join(os.path.dirname(export_destination_path), "Common", team_id)):
            dummy_kits_replace(team_id, team_name)

        # Delete the now empty export folder
        shutil.rmtree(export_destination_path)

        print("-")

    if dds_compression and not fox_mode:
        # zlib compress all the dds files
        print("- Compressing dds files...")
        print("-")
        zlib_files_in_folder(main_destination_path, "dds")

    print("- Done")
    print("-")

    if not all_in_one:
        log_presence_warn()
        print("-")

    # Check if the Other folder exists and there are files in it, if there are print a warning
    other_path = os.path.join(EXTRACTED_PATH, "Other")
    if os.path.exists(other_path) and len(os.listdir(other_path)) > 0:
        print( "-")
        print(f"- {COLORS.DARK_CYAN}Info{COLORS.RESET}: There are files in the Other folder")
        print( "- Please open it and check its contents")
        if pause_on_error:
            print("-")
            pause()
