import os
import shutil
import filecmp
import logging

from .utils.pausing import pause


def portraits_move(exportfolder_path, team_id):
    """
    Move player portraits from the Faces folder to the Portraits folder based on specific conditions.

    Parameters:
    - exportfolder_path (str): The path to the main export folder.
    - team_id (str): The team id used to generate player ids.

    Returns:
    - bool: True if there are conflicts in portrait names, False otherwise.
    """

    # Read the necessary parameters
    pause_allow = int(os.environ.get('PAUSE_ALLOW', '1'))

    TEX_NAME = "portrait.dds"

    portrait_conflicts = []
    portraits_path = os.path.join(exportfolder_path, "Portraits")

    faces_path = os.path.join(exportfolder_path, "Faces")
    for face_name in [f for f in os.listdir(faces_path) if os.path.isdir(os.path.join(faces_path, f))]:

        # Check that the player number is a number within the 01-23 range
        if not (face_name[3:5].isdigit() and '01' <= face_name[3:5] <= '23'):
            continue

        # Check if the folder has a portrait
        face_path = os.path.join(faces_path, face_name)
        portrait_path = os.path.join(face_path, TEX_NAME)
        if not os.path.exists(portrait_path):
            continue

        player_number = face_name[3:5]
        player_id = team_id + player_number

        # Create a folder for portraits if not present
        if not os.path.exists(portraits_path):
            os.makedirs(portraits_path)

        # Rename the portrait with the player id
        portrait_name = f"player_{player_id}.dds"

        # Check if a file with the same player number already exists in the portraits folder
        existing_portrait = next((f for f in os.listdir(portraits_path) if f[-6:-4] == player_number), None)
        if existing_portrait:
            portrait_destination_path = os.path.join(portraits_path, existing_portrait)

            # Check if the portait files have the same contents
            if not (os.path.exists(portrait_destination_path) and
                    filecmp.cmp(portrait_path, portrait_destination_path)):

                # If they do not, add the face name to the list of conflicts
                portrait_conflicts.append(face_name)
            else:
                # If they do, delete the portrait
                os.remove(portrait_path)

        else:
            # Move the portrait to the portraits folder
            portrait_destination_path = os.path.join(portraits_path, portrait_name)
            os.rename(portrait_path, portrait_destination_path)

        # Check if the "ingame_face" file is present and delete the folder if it is
        ingame_face_path = os.path.join(face_path, "ingame_face")
        ingame_face_txt_path = os.path.join(face_path, "ingame_face.txt")
        if os.path.exists(ingame_face_path) or os.path.exists(ingame_face_txt_path):
            shutil.rmtree(face_path)

    # If there are any portrait conflicts
    if portrait_conflicts:

        exportfolder_name = os.path.basename(exportfolder_path)

        logging.error( "-")
        logging.error( "- ERROR - Conflicting portraits")
        logging.error(f"- Export name:    {exportfolder_name}")
        logging.error( "- The portraits for the following players are present both")
        logging.error( "- in their face folders and in the Portraits folder:")
        # logging.error the list of portrait conflicts
        for portrait in portrait_conflicts:
            logging.error(f"- {portrait}")
        logging.error( "- The entire export will be skipped")

        if pause_allow:
            print("-")
            pause()

        # Delete the entire export folder
        shutil.rmtree(exportfolder_path)

        # Exit with error
        return True

    return False