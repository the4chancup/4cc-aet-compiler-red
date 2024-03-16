import os
import shutil

# Read the necessary parameters
pass_through = int(os.environ.get('PASS_THROUGH', '0'))
pause_when_wrong = int(os.environ.get('PAUSE_WHEN_WRONG', '1'))

# Function for finding the team ID after receiving the foldername as parameter
def teamid_get(exportfolder_path, team_name):

    # Define team_raw as team_name without the slashes at the start and end
    team_raw = team_name[1:-1].upper()
    
    root_found = None
    not_root = None
    error = None
    teamid = None

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
        root_found = 1


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
                root_found = 1
                not_root = 1
                foldername_inside = foldername_test
    
    # If there's no files anywhere
    if not root_found:
      
        # Skip the whole export
        ##if pass_through != 1:

        error = 1
        shutil.rmtree(exportfolder_path)

        with open('memelist.txt', 'a') as file:
            file.write("-\n")
            file.write("- {}'s manager needs to get memed on (no files) - Export discarded.\n".format(team_name))
        memelist = 1

        ##if pause_when_wrong != 0:

        print("-\n")
        print("- {}'s manager needs to get memed on (no files).".format(team_name))
        print("- This export will be discarded.\n")
        print("- Closing the script's window and fixing the export is recommended.\n")

        input()

    # If the export is usable, continue
    if not error:
    
        # Reset the flag for usable team name found
        team_name_good = None
    
        # If the folders are not at the root
        if not_root:
    
            # Move the stuff to the root
            for file in os.listdir(f"{exportfolder_path}/{foldername_inside}"):
                shutil.move(f"{exportfolder_path}/{foldername_inside}/{file}", exportfolder_path)
    
            # Delete the now empty folder
            shutil.rmtree(f"{exportfolder_path}/{foldername_inside}")
    
        # Look for a txt file with Note in the filename
        note_found = None
        for file in os.listdir(exportfolder_path):
            if file.endswith(".txt") and "Note" in file:
                note_found = True
                note_name = f"{team_raw} Note.txt"
                os.rename(f"{exportfolder_path}/{file}", f"{exportfolder_path}/{note_name}")
    
        # If there's a Note file try to get the team name from it
        if note_found:
    
            team_name_found = None
            with open(f"{exportfolder_path}/{note_name}", 'r') as file:
                for line in file:
                    if not team_name_found:
                        if "Team:" in line:
                            team_name_found = True
                            team_name = line.split(":", 1)[1].strip()
    
            if team_name_found:
    
                # If the name on the note file is different than the one on the export foldername print it
                if team_name.lower() != team_name.lower():
                    print(f"- Actual name: {team_name}")
    
                # Search for the team ID on the list of team names
                with open("./teams_list.txt", 'r') as team_file:
                    for line in team_file.readlines()[1:]:
                        if not team_name_good:
                            if team_name.lower() == line.split()[1].lower():
                                teamid = line.split()[0]
                                team_name_good = True
    
        # If there's no Note file or no usable team name was found on it
        if not team_name_good:
    
            # Check if the team name taken from the export foldername with brackets added is on the list
            with open("./teams_list.txt", 'r') as team_file:
                for line in team_file.readlines()[1:]:
                    if not team_name_good:
                        if team_name.lower() == line.split()[1].lower():
                            teamid = line.split()[0]
                            team_name_good = True
    
        # If no usable team name was found even then
        if not team_name_good:
    
            # Skip the whole export
            if not pass_through:
                shutil.rmtree(exportfolder_path)
    
            with open("memelist.txt", 'a') as memelist:
                memelist.write(f"\n- {team_name}'s manager needs to get memed on (unusable team name) - Export discarded.")
            
            print(f"- {team_name}'s manager needs to get memed on (unusable team name).")
            print("- The team name was not found on the teams_list txt file.")
            print("- This export will be discarded to prevent conflicts.")
            print("- Adding the team name to the teams_list file and")
            print("- restarting the script is recommended.")
            
            if pause_when_wrong:
                input("Press Enter to continue...")
            
        else:
            print(f"(ID: {teamid})")

    return teamid