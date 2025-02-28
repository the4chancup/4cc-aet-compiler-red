import os
import shutil
import filecmp
import logging

from .texture_check import textures_convert
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
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    fox_19 = (int(os.environ.get('PES_VERSION', '19')) >= 19)
    pause_on_error = int(os.environ.get('PAUSE_ON_ERROR', '1'))

    TEX_NAME = "portrait.dds"

    portrait_conflicts = []
    portraits_path = os.path.join(exportfolder_path, "Portraits")

    faces_path = os.path.join(exportfolder_path, "Faces")
    for face_name in [f for f in os.listdir(faces_path) if os.path.isdir(os.path.join(faces_path, f))]:

        # Check that the player number is a number within the 01-23 range
        if face_name[3:5].isdigit() and '01' <= face_name[3:5] <= '23':

            # If the folder has a portrait
            portrait_path = os.path.join(faces_path, face_name, TEX_NAME)
            if os.path.exists(portrait_path):

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

        if pause_on_error:
            print("-")
            pause()

        # Delete the entire export folder
        shutil.rmtree(exportfolder_path)

        # Exit with error
        return True

    # Convert the portraits if needed
    if os.path.exists(portraits_path):
        textures_convert(portraits_path, fox_mode, fox_19)

    return False