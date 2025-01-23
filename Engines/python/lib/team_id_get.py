import os
import shutil
import logging

from .utils.file_management import file_critical_check
from .utils.pausing import pause
from .utils.FILE_INFO import TEAMS_LIST_PATH


def id_search(team_name):

    with open(TEAMS_LIST_PATH, 'r', encoding="utf8") as team_file:
        for line in team_file.readlines()[1:]:
            parts = line.split()
            if len(parts) < 2:
                continue
            if team_name.lower() == parts[1].lower():
                team_id = parts[0]
                break
        else:
            team_id = None

    return team_id


def export_files_present(directory_path: str) -> bool:
    """Check if the directory contains any export-related files or folders."""
    return any([
        any(f.endswith('.txt') for f in os.listdir(directory_path)),
        os.path.exists(f"{directory_path}/Faces"),
        os.path.exists(f"{directory_path}/Kit Configs"),
        os.path.exists(f"{directory_path}/Kit Textures"),
        os.path.exists(f"{directory_path}/Portraits"),
        os.path.exists(f"{directory_path}/Boots"),
        os.path.exists(f"{directory_path}/Gloves"),
        os.path.exists(f"{directory_path}/Collars"),
        os.path.exists(f"{directory_path}/Logo"),
        os.path.exists(f"{directory_path}/Common"),
        os.path.exists(f"{directory_path}/Other")
    ])


# Function for finding the team ID after receiving the foldername as parameter
def team_id_get(exportfolder_path, team_name_folder: str, team_id_min, team_id_max):

    # Check if the teams list file exists
    file_critical_check(TEAMS_LIST_PATH)

    # Read the necessary parameters
    pause_on_error = int(os.environ.get('PAUSE_ON_ERROR', '1'))

    root_found = None
    not_root = None
    team_id = None

    if export_files_present(exportfolder_path):
        root_found = True

    # If the folders aren't at the root
    if not root_found:

        # Look in every folder for a faces or kit configs folder
        for foldername_test in os.listdir(exportfolder_path):
            test_path = os.path.join(exportfolder_path, foldername_test)

            if export_files_present(test_path):
                root_found = True
                not_root = True
                foldername_inside = foldername_test
                break

    # If there's no usable files anywhere
    if not root_found:

        logging.error( "-")
        logging.error( "- ERROR - No usable files found")
        logging.error(f"- Team name:      {team_name_folder}")
        logging.error( "- This export will be discarded")

        # Skip the whole export
        shutil.rmtree(exportfolder_path)

        if pause_on_error:
            print("-")
            pause()

        return None, None

    # If the folders are not at the root
    if not_root:

        # Move the stuff to the root
        for file in os.listdir(f"{exportfolder_path}/{foldername_inside}"):
            shutil.move(f"{exportfolder_path}/{foldername_inside}/{file}", exportfolder_path)

        # Delete the now empty folder
        shutil.rmtree(f"{exportfolder_path}/{foldername_inside}")

    # Look for a txt file with Note in the filename
    note_name = None
    for file in os.listdir(exportfolder_path):
        if file.endswith(".txt") and "note" in file.lower():
            note_name = file
            break

    team_id = None
    team_name = None

    # If there's a Note file try to get the team name from it
    if note_name:

        with open(f"{exportfolder_path}/{note_name}", 'r', encoding="utf8") as file:
            for line in file:
                if "Team:" in line:
                    team_name = line.split(":", 1)[1].strip()
                    break

    if team_name:

        # Rename the Note file with a clean version of the team name without slashes
        team_name_clean = team_name.replace("/", "").replace("\\", "").upper()
        note_name_new = f"{team_name_clean} Note.txt"

        if note_name_new != note_name:
            try:
                os.rename(f"{exportfolder_path}/{note_name}", f"{exportfolder_path}/{note_name_new}")
            except FileExistsError:
                logging.error( "-")
                logging.error( "- ERROR - Duplicate Note file found")
                logging.error(f"- Team name:      {team_name_folder}")
                logging.error( "- This export will be discarded")

                if pause_on_error:
                    print("-")
                    pause()

                # Skip the whole export
                shutil.rmtree(exportfolder_path)

                return None, None

        # If the name on the Note file is different than the one on the export foldername print it
        if team_name.lower() != team_name_folder.lower():
            print(f"- Actual name: {team_name} ", end='')

    # If there's no Note file or no usable team name was found on it
    else:

        # Use the team name taken from the export foldername
        team_name = team_name_folder

    # Search for the team ID on the list of team names
    team_id = id_search(team_name)

    # If no usable team name was found even then
    if not team_id:
        print("")
        logging.error( "-")
        logging.error( "- ERROR - Unusable team name")
        logging.error(f"- Team name:      {team_name}")
        logging.error( "- The team name was not found on the teams list file")

        while True:
            print("-")
            team_id_new = input("- Enter a team ID for this team (or press Enter to skip the export): ")

            if not team_id_new.strip():
                break

            if not team_id_new.isdigit() or int(team_id_new) not in range(team_id_min, team_id_max + 1):
                print(f"- Error: Team ID must be a number between {team_id_min} and {team_id_max}")
                continue

            # Search for the line with the team ID on the list of team names and print it
            with open(TEAMS_LIST_PATH, 'r', encoding="utf8") as f:
                for line in f.readlines()[1:]:
                    if line.split()[0] == team_id_new:
                        team_name_old = ' '.join(line.split()[1:])
                        print(f"- Team ID {team_id_new} is already in use by {team_name_old}")
                        response = input("- Do you want to overwrite it? (Enter to confirm, \"no\" to try again): ")
                        break
                else:
                    response = "yes"

            if response.strip().lower() == "no":
                continue

            # Add the new team ID to teams_list.txt
            with open(TEAMS_LIST_PATH, 'r+', encoding="utf8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if line.startswith(f"{team_id_new} "):
                        lines[i] = f"{team_id_new} {team_name}\n"
                        break
                else:
                    lines.append(f"{team_id_new} {team_name}\n")
                f.seek(0)
                f.writelines(lines)
                f.truncate()

            team_id = team_id_new
            logging.error(f"- Added team {team_name} with ID {team_id} to the teams list file")
            print("-")
            print(f"- {team_name} (ID: {team_id})")

            return team_id, team_name

        logging.error( "- This export will be discarded to prevent conflicts")

        if pause_on_error:
            print("-")
            pause()

        # Skip the whole export
        shutil.rmtree(exportfolder_path)

        return None, None

    print(f"(ID: {team_id})")

    # Check if the team ID is in the range
    if not (team_id.isdigit() and int(team_id) in range(team_id_min, team_id_max + 1)):

        logging.error( "-")
        logging.error( "- ERROR - Team ID out of range")
        logging.error(f"- Team name:      {team_name}")
        logging.error(f"- Team ID:        {team_id}")
        logging.error(f"- The team ID is not in the range {team_id_min} - {team_id_max}")
        logging.error( "- This export will be discarded to prevent conflicts")

        # Skip the whole export
        shutil.rmtree(exportfolder_path)

        return None, None

    return team_id, team_name
