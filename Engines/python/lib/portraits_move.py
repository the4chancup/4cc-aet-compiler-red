import os

# Function for finding the team ID after receiving the foldername as parameter
def portraits_move(exportfolder_path, team_id):

    tex_name = "portrait.dds"

    faces_path = os.path.join(exportfolder_path, "Faces")
    for face_name in os.listdir(faces_path):

        # Check that the player number is a number within the 01-23 range
        if face_name[3:5].isdigit() and '01' <= face_name[3:5] <= '23':

            # If the folder has a portrait
            portrait_path = os.path.join(faces_path, face_name, tex_name)
            if os.path.exists(portrait_path):

                face_id = team_id + face_name[3:5]

                # Create a folder for portraits if not present
                portraits_path = os.path.join(exportfolder_path, "Portraits")
                if not os.path.exists(portraits_path):
                    os.makedirs(portraits_path)

                # Rename the portrait with the player id and move it to the portraits folder
                portrait_name = f"player_{face_id}.dds"
                
                os.rename(portrait_path, os.path.join(portraits_path, portrait_name))

        # Check if the folder is now empty
        if not os.listdir(os.path.join(faces_path, face_name)):
            # If empty remove it
            os.rmdir(os.path.join(faces_path, face_name))