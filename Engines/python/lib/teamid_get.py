import os
import shutil
import logging

from .file_management import file_critical_check


# Function for finding the team ID after receiving the foldername as parameter
def teamid_get(exportfolder_path, team_name_folder, team_id_min, team_id_max):

    TEAMS_LIST_FILE = "teams_list.txt"

    # Check if the teams list file exists
    file_critical_check(TEAMS_LIST_FILE)

    # Read the necessary parameters
    pause_on_error = int(os.environ.get('PAUSE_ON_ERROR', '1'))

    # Prepare a clean version of the team name without slashes
    team_name_folder_clean = team_name_folder.replace("/", "").replace("\\", "").upper()

    root_found = None
    not_root = None
    team_id = None

    if any([
        os.path.exists(f"{exportfolder_path}/*.txt"),
        os.path.exists(f"{exportfolder_path}/Faces"),
        os.path.exists(f"{exportfolder_path}/Kit Configs"),
        os.path.exists(f"{exportfolder_path}/Kit Textures"),
        os.path.exists(f"{exportfolder_path}/Portraits"),
        os.path.exists(f"{exportfolder_path}/Boots"),
        os.path.exists(f"{exportfolder_path}/Gloves"),
        os.path.exists(f"{exportfolder_path}/Collars"),
        os.path.exists(f"{exportfolder_path}/Logo"),
        os.path.exists(f"{exportfolder_path}/Common"),
        os.path.exists(f"{exportfolder_path}/Other")
    ]):
        root_found = True


    # If the folders aren't at the root
    if not root_found:

        # Look in every folder for a faces or kit configs folder
        for foldername_test in os.listdir(exportfolder_path):
            if any([
                os.path.exists(f"{exportfolder_path}/{foldername_test}/*.txt"),
                os.path.exists(f"{exportfolder_path}/{foldername_test}/Faces"),
                os.path.exists(f"{exportfolder_path}/{foldername_test}/Kit Configs"),
                os.path.exists(f"{exportfolder_path}/{foldername_test}/Kit Textures"),
                os.path.exists(f"{exportfolder_path}/{foldername_test}/Portraits"),
                os.path.exists(f"{exportfolder_path}/{foldername_test}/Boots"),
                os.path.exists(f"{exportfolder_path}/{foldername_test}/Gloves"),
                os.path.exists(f"{exportfolder_path}/{foldername_test}/Collars"),
                os.path.exists(f"{exportfolder_path}/{foldername_test}/Logo"),
                os.path.exists(f"{exportfolder_path}/{foldername_test}/Common"),
                os.path.exists(f"{exportfolder_path}/{foldername_test}/Other")
            ]):
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
            input("Press Enter to continue...")

        return None


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
            note_name = f"{team_name_folder_clean} Note.txt"
            os.rename(f"{exportfolder_path}/{file}", f"{exportfolder_path}/{note_name}")
            break

    team_id = None

    # If there's a Note file try to get the team name from it
    if note_name:

        team_name = None
        with open(f"{exportfolder_path}/{note_name}", 'r', encoding="utf8") as file:
            for line in file:
                if "Team:" in line:
                    team_name = line.split(":", 1)[1].strip()
                    break

        if team_name:

            # If the name on the note file is different than the one on the export foldername print it
            if team_name.lower() != team_name_folder.lower():
                print(f"- Actual name: {team_name} ", end='')

            # Search for the team ID on the list of team names
            with open(TEAMS_LIST_FILE, 'r') as team_file:
                for line in team_file.readlines()[1:]:
                    if team_name.lower() == line.split()[1].lower():
                        team_id = line.split()[0]
                        break

    # If there's no Note file or no usable team name was found on it
    if not team_id:

        # Check if the team name taken from the export foldername with brackets added is on the list
        with open(TEAMS_LIST_FILE, 'r') as team_file:
            for line in team_file.readlines()[1:]:
                if team_name_folder.lower() == line.split()[1].lower():
                    team_id = line.split()[0]
                    break

    # If no usable team name was found even then
    if not team_id:

        logging.error( "-")
        logging.error( "- ERROR - Unusable team name")
        logging.error(f"- Team name:      {team_name}")
        logging.error( "- The team name was not found on the teams list file.")
        logging.error( "- This export will be discarded to prevent conflicts.")
        logging.error(f"- Add the team name to the \"{TEAMS_LIST_FILE}\" file and restart")

        if pause_on_error:
            input("Press Enter to continue...")

        # Skip the whole export
        shutil.rmtree(exportfolder_path)

        return None

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

        return None

    return team_id