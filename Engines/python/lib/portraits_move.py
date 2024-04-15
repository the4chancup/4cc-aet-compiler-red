import os
import shutil

# Function for finding the team ID after receiving the foldername as parameter
def portraits_move(exportfolder_path, team_id):

    tex_name = "portrait.dds"

    portrait_conflicts = []

    faces_path = os.path.join(exportfolder_path, "Faces")
    for face_name in [f for f in os.listdir(faces_path) if os.path.isdir(os.path.join(faces_path, f))]:

        # Check that the player number is a number within the 01-23 range
        if face_name[3:5].isdigit() and '01' <= face_name[3:5] <= '23':

            # If the folder has a portrait
            portrait_path = os.path.join(faces_path, face_name, tex_name)
            if os.path.exists(portrait_path):

                player_number = face_name[3:5]
                player_id = team_id + player_number

                # Create a folder for portraits if not present
                portraits_path = os.path.join(exportfolder_path, "Portraits")
                if not os.path.exists(portraits_path):
                    os.makedirs(portraits_path)

                # Rename the portrait with the player id
                portrait_name = f"player_{player_id}.dds"

                # Check if a file with the same player number already exists in the portraits folder
                if any(fname[-6:-4] == player_number for fname in os.listdir(portraits_path)):

                    # Add the face name to the list of conflicts
                    portrait_conflicts.append(face_name)

                else:
                    # Move the portrait to the portraits folder
                    portrait_destination_path = os.path.join(portraits_path, portrait_name)
                    os.rename(portrait_path, portrait_destination_path)

        # Check if the folder is now empty
        if not os.listdir(os.path.join(faces_path, face_name)):
            # If empty remove it
            os.rmdir(os.path.join(faces_path, face_name))

    # If there are any portrait conflicts
    if portrait_conflicts:

        print("- The portraits for the following players are present both")
        print("- in their face folders and in the Portraits folder:")
        # Print the list of portrait conflicts
        print("- " + "\n- ".join(portrait_conflicts))
        print("- The entire export will be skipped.")
        print("- Closing the script's window and fixing it is recommended.")
        print("-")
        input("Press Enter to continue...")

        exportfolder_name = os.path.basename(exportfolder_path)

        with open("memelist.txt", "a") as log:
            log.write("- \n")
            log.write(f"- {exportfolder_name} Deleted (conflicting portraits) - Error\n")

        os.environ["LOG"] = "1"

        # Delete the entire export folder
        shutil.rmtree(exportfolder_path)

        # Exit with error
        return True

    return False