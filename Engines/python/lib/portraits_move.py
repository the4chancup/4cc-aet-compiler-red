import os
import shutil
import filecmp
import logging

from .utils.pausing import pause


def portraits_move(exportfolder_path, team_id, folder_slots=None, delete_on_ingame_face=True):
    """
    Move player portraits from the face folders to the Portraits folder based on specific conditions.

    Parameters:
    - exportfolder_path (str): The path to the main export folder.
    - team_id (str): The team id used to generate player ids.
    - folder_slots (list, optional): List of (folder_path, slots) tuples to scan instead of
      the Faces/* folders (new-format player folders, slots from the roster, several per
      folder when multi-mapped). When given, one portrait per slot is emitted and nothing
      is ever deleted.
    - delete_on_ingame_face (bool): Whether an "ingame_face" marker deletes the folder
      (old-format behavior; new-format player folders are never deleted here).

    Returns:
    - bool: True if there are conflicts in portrait names, False otherwise.
    """

    TEX_SUFFIX = "portrait.dds"

    portrait_conflicts = []
    portraits_folder_path = os.path.join(exportfolder_path, "Portraits")

    if folder_slots is None:
        faces_folder_path = os.path.join(exportfolder_path, "Faces")
        folder_slots = [
            (os.path.join(faces_folder_path, folder_name), [folder_name[3:5]])
            for folder_name in os.listdir(faces_folder_path)
            if os.path.isdir(os.path.join(faces_folder_path, folder_name))
        ]

    for folder_path, slots in folder_slots:

        # Check that the player number is a number within the 01-23 range
        if delete_on_ingame_face:
            folder_name = os.path.basename(folder_path)
            if not (folder_name[3:5].isdigit() and '01' <= folder_name[3:5] <= '23'):
                continue

        # Check if the folder has a portrait
        file_name_list = os.listdir(folder_path)
        for file_name in file_name_list:
            if file_name.lower().endswith(TEX_SUFFIX):
                portrait_path = os.path.join(folder_path, file_name)
                break
        else:
            continue

        # Create a folder for portraits if not present
        if not os.path.exists(portraits_folder_path):
            os.makedirs(portraits_folder_path)

        folder_had_conflict = False

        for player_number in slots:
            player_id = team_id + player_number

            # Check if a file with the same player number already exists in the portraits folder
            existing_portrait = next((f for f in os.listdir(portraits_folder_path) if f[-6:-4] == player_number), None)
            if existing_portrait:
                portrait_destination_path = os.path.join(portraits_folder_path, existing_portrait)

                # Check if the portait files have the same contents
                if not (os.path.exists(portrait_destination_path) and
                        filecmp.cmp(portrait_path, portrait_destination_path)):

                    # If they do not, add the face name to the list of conflicts
                    portrait_conflicts.append(os.path.basename(folder_path))
                    folder_had_conflict = True

            else:
                # Copy the portrait to the portraits folder with the player id name
                portrait_destination_path = os.path.join(portraits_folder_path, f"player_{player_id}.dds")
                shutil.copy(portrait_path, portrait_destination_path)

        # The portrait always leaves the folder it was found in (a conflict discards
        # the whole export anyway, so the source file's fate does not matter then)
        if not folder_had_conflict:
            os.remove(portrait_path)

        # Check if the "ingame_face" file is present and delete the folder if it is
        if delete_on_ingame_face:
            ingame_face_path = os.path.join(folder_path, "ingame_face")
            ingame_face_txt_path = os.path.join(folder_path, "ingame_face.txt")
            if os.path.exists(ingame_face_path) or os.path.exists(ingame_face_txt_path):
                shutil.rmtree(folder_path)

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
        logging.error( "- (Or their face folders are repeated)")
        logging.error( "-")
        logging.error( "- The entire export will be skipped")

        pause()

        # Delete the entire export folder
        shutil.rmtree(exportfolder_path)

        # Exit with error
        return True

    return False
