## Checks the export for all kinds of errors
import os
import shutil
import logging

from .utils.pausing import pause
from .texture_check import texture_check
from .xml_check import mtl_check
from .xml_check import xml_check
from .xml_check import face_diff_xml_check
from .txt_kits_count import txt_kits_count



FILE_TYPE_ALLOWED_LIST = [
    ".bin",
    ".xml",
    ".fmdl",
    ".model",
    ".mtl",
    ".dds",
    ".ftex",
    ".skl",
]

PREFOX_FILE_TYPE_DISALLOWED_LIST = [
    ".fmdl",
    ".ftex",
    ".skl",
]

FOX_FILE_TYPE_DISALLOWED_LIST = [
    ".model",
    ".mtl",
]


# Check for nested folders with repeating names
def nested_folders_fix(exportfolder_path, team_name):

    # Variable to store whether nested folders were found
    nested_error = None

    # Make a list of all the folders in the export folder
    folders = [f for f in os.listdir(exportfolder_path) if os.path.isdir(os.path.join(exportfolder_path, f))]

    # Loop through each folder
    for folder_name in folders:

        # Get the path of the directory
        folder_path = os.path.join(exportfolder_path, folder_name)

        # Get the path of a subdirectory that has the same name as its parent folder
        subfolder_path = os.path.join(folder_path, folder_name)

        # Check if it exists and is not the 'Other' or 'Common' folder
        if os.path.isdir(subfolder_path) and folder_name not in ("Other", "Common"):

            nested_error = True

            # Create a temporary folder path in the main export folder
            temp_path = os.path.join(exportfolder_path, "Temp")
            os.makedirs(temp_path, exist_ok=True)

            # Loop through each item in the subdirectory and move it to the temporary folder
            for item_name in os.listdir(subfolder_path):
                shutil.move(os.path.join(subfolder_path, item_name), temp_path)

            # Delete the now empty subdirectory
            shutil.rmtree(subfolder_path)

            # Loop through each file in the temporary folder and move it to the proper folder
            for item_name in os.listdir(temp_path):
                shutil.move(os.path.join(temp_path, item_name), folder_path)

            # Delete the temporary folder
            shutil.rmtree(temp_path)

    # If some folders were nested, warn about it
    if nested_error:

        logging.warning( "-")
        logging.warning( "- Warning - Nested folders")
        logging.warning(f"- Team name:      {team_name}")
        logging.warning( "- An attempt to automatically fix those folders has been made")
        logging.warning( "- Nothing has been discarded, but problems may still arise")


def faces_check(exportfolder_path, team_name, team_id):
    itemfolder_path = os.path.join(exportfolder_path, "Faces")

    # Check if the folder exists
    if not os.path.isdir(itemfolder_path):
        return

    # If the folder is empty, delete it
    if not os.listdir(itemfolder_path):
        shutil.rmtree(itemfolder_path)
        return

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    strict_file_type_check = int(os.environ.get('STRICT_FILE_TYPE_CHECK', '1'))

    folder_error_any = None
    player_num_list = []

    # Prepare a list of subfolders
    subfolder_list = [subfolder for subfolder in os.listdir(itemfolder_path) if os.path.isdir(os.path.join(itemfolder_path, subfolder))]

    # For every subfolder
    for subfolder_name in subfolder_list:

        subfolder_path = os.path.join(itemfolder_path, subfolder_name)

        # Initialize error subflags
        folder_error_num_bad = False
        folder_error_num_repeated = False
        folder_error_edithairxml = False
        folder_error_hairxml = False
        folder_error_xml_format = False
        folder_error_tex_format = False
        folder_error_mtl_format = False
        folder_error_file_disallowed_list = []

        # Check player numbers differently for referee exports
        if team_name == "/refs/":
            # For referees, face folders should be refereeXXX where XXX is 001-035
            if not subfolder_name.startswith("referee"):
                folder_error_num_bad = True
            else:
                try:
                    player_num = subfolder_name[7:10]  # Get number after "referee"
                    folder_error_num_bad = not all((
                        subfolder_name.startswith("referee"),
                        player_num.isdigit(),
                        1 <= int(player_num) <= 35
                    ))
                except Exception:
                    folder_error_num_bad = True
        else:
            # For teams, face folders should be XXXxx where xx is 01-23
            try:
                player_num = subfolder_name[3:5] # Get number after the team ID's placeholder
                folder_error_num_bad = not all((
                    player_num.isdigit(),
                    1 <= int(player_num) <= 23
                ))
            except Exception:
                folder_error_num_bad = True

        # Check if the player number is already in the list
        if player_num in player_num_list:
            folder_error_num_repeated = True

        player_num_list.append(player_num)

        if not fox_mode:
            # Check if the folder has a face.xml or the unsupported face_edithair.xml and hair.xml
            face_xml_path = os.path.join(subfolder_path, "face.xml")
            face_diff_xml_path = os.path.join(subfolder_path, "face_diff.xml")
            face_edithair_xml_path = os.path.join(subfolder_path, "face_edithair.xml")
            hair_xml_path = os.path.join(subfolder_path, "hair.xml")
            if os.path.isfile(face_edithair_xml_path):
                folder_error_edithairxml = True
            elif os.path.isfile(hair_xml_path):
                folder_error_hairxml = True
            elif os.path.isfile(face_xml_path):
                folder_error_xml_format = xml_check(face_xml_path, team_id)
            elif os.path.isfile(face_diff_xml_path):
                folder_error_xml_format = face_diff_xml_check(face_diff_xml_path)

        # Check every texture
        for texture_name in os.listdir(subfolder_path):
            texture_path = os.path.join(subfolder_path, texture_name)

            if texture_check(texture_path):
                folder_error_tex_format = True

        # Check every mtl file
        if not fox_mode:
            for mtl_name in [f for f in os.listdir(subfolder_path) if f.endswith(".mtl")]:
                mtl_path = os.path.join(subfolder_path, mtl_name)

                if mtl_check(mtl_path, team_id):
                    folder_error_mtl_format = True

        # Make a list with the allowed and disallowed file types
        file_type_disallowed_list = PREFOX_FILE_TYPE_DISALLOWED_LIST if not fox_mode else FOX_FILE_TYPE_DISALLOWED_LIST
        file_type_allowed_list_filtered = [
            file_type for file_type in FILE_TYPE_ALLOWED_LIST if file_type not in file_type_disallowed_list
        ]
        # Check if any file is disallowed
        for file_name in [f for f in os.listdir(subfolder_path) if os.path.isfile(os.path.join(subfolder_path, f))]:
            file_type = os.path.splitext(file_name)[1].lower()
            if file_type not in file_type_allowed_list_filtered:
                folder_error_file_disallowed_list.append(file_name)

        if folder_error_file_disallowed_list:
            # Determine log level based on the parameter
            if strict_file_type_check:
                log_level = logging.ERROR
                level_text = "ERROR"
                action_text = "This folder will be discarded"
            else:
                log_level = logging.INFO
                level_text = "Info"
                action_text = "Consider removing these files for better compatibility"

            allowed_file_types = ", ".join(file_type_allowed_list_filtered)

            logging.log(log_level, "-")
            logging.log(log_level, f"- {level_text} - Disallowed files")
            logging.log(log_level, f"- Team name:          {team_name}")
            logging.log(log_level, f"- Face folder:        {subfolder_name}")
            for file_name in folder_error_file_disallowed_list:
                logging.log(log_level, f"- File name:          {file_name}")
            logging.log(log_level, f"- Allowed file types: {allowed_file_types}")
            logging.log(log_level, "-")
            logging.log(log_level, f"- {action_text}")

            # If strict file type check is disabled, clear the list
            if not strict_file_type_check:
                folder_error_file_disallowed_list = []

        # Set the main flag if any of the checks failed
        folder_error = any((
            folder_error_num_bad,
            folder_error_num_repeated,
            folder_error_edithairxml,
            folder_error_hairxml,
            folder_error_xml_format,
            folder_error_tex_format,
            folder_error_mtl_format,
            folder_error_file_disallowed_list,
        ))

        # If the face folder has something wrong
        if folder_error:

            # Warn about the team having bad folders
            if not folder_error_any:
                logging.error( "-")
                logging.error( "- ERROR - Bad face folders")
                logging.error(f"- Team name:      {team_name}")
                folder_error_any = True

            logging.error(f"- Face folder:    {subfolder_name}")

            # Give an error depending on the particular problem
            if folder_error_num_bad:
                logging.error(f"- (player number {subfolder_name[3:5]} outside the 01-23 range)")
            if folder_error_num_repeated:
                logging.error(f"- (player number {subfolder_name[3:5]} already in use)")
            if folder_error_xml_format:
                logging.error( "- (broken xml file)")
            if folder_error_edithairxml:
                logging.error( "- (unsupported edithair face folder, needs updating)")
            if folder_error_hairxml:
                logging.error( "- (unsupported hair xml inside, needs updating)")
            if folder_error_tex_format:
                logging.error( "- (bad textures)")
            if folder_error_mtl_format:
                logging.error( "- (broken mtl files)")
            if folder_error_file_disallowed_list:
                for file_name in folder_error_file_disallowed_list:
                    logging.error(f"- ({file_name} is not allowed)")

            # And skip it
            shutil.rmtree(subfolder_path)

    # If there were any bad folders
    if folder_error_any:

        logging.error( "-")
        logging.error( "- These face folders will be discarded to avoid problems")

        if pause_allow:
            print("-")
            pause()


# If a Kit Configs folder exists and is not empty, check that the amount of kit config files is correct
def kitconfigs_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Kit Configs")

    # Check if the folder exists
    if not os.path.isdir(itemfolder_path):
        return

    # If the folder is empty, delete it
    if not os.listdir(itemfolder_path):
        shutil.rmtree(itemfolder_path)
        return

    # Initialize the error flag
    file_error = False

    # Check if the files are in an inner folder
    for subitem_name in os.listdir(itemfolder_path):
        subitem_path = os.path.join(itemfolder_path, subitem_name)
        if os.path.isdir(subitem_path):

            # If a folder was found move its contents to the root folder
            for file in os.listdir(subitem_path):
                shutil.move(os.path.join(subitem_path, file), itemfolder_path)

            # And delete the now empty folder
            shutil.rmtree(subitem_path)

    config_count = len(os.listdir(itemfolder_path))
    config_list = []

    # For every file
    for file_name in os.listdir(itemfolder_path):

        #TODO: Check if these checks are really case-insensitive
        # Check the DEF part of the name
        if not file_name[3:8].lower() == "_def_":#DEF?
            file_error = True
            break
        # Check the realUni part
        if not file_name[-12:].lower() == "_realuni.bin":#realUni?
            file_error = True
            break

        # Prepare the name without the team ID
        config_name_base = file_name[3:].lower()

        # Check if the name is in the list
        if config_name_base in config_list:
            file_error = True
            break

        config_list.append(file_name[3:].lower())

    # If any file was wrong
    if file_error:

        # Skip the whole folder
        shutil.rmtree(os.path.join(exportfolder_path, "Kit Configs"))

        # Log the issue
        logging.error( "-")
        logging.error( "- ERROR - Wrong kit config names")
        logging.error(f"- Team name:      {team_name}")
        logging.error( "- The Kit Configs folder will be discarded since it's unusable")
        logging.error( "- Check the AET wikipage for the proper naming convention")

        # Pause if needed
        if pause_allow:
            print("-")
            pause()

        return

    # Prepare a clean version of the team name without slashes
    team_name_clean = team_name.replace("/", "").replace("\\", "").upper()

    # Path to the txt file with the team"s name
    note_path = os.path.join(exportfolder_path, f"{team_name_clean} Note.txt")

    # Check if the txt file exists
    if os.path.exists(note_path):

        # Check that the number of kit configs and kit color entries in the Note txt are the same
        config_count_note = txt_kits_count(note_path)
        if config_count_note != config_count:

            logging.warning( "-")
            logging.warning( "- Warning - Missing kit configs or txt kit color entries")
            logging.warning(f"- Team name:      {team_name}")
            logging.warning(f"- The number of kit config files ({config_count}) is not equal to")
            logging.warning(f"- the number of kit color entries ({config_count_note}) in the Note txt file")


# If a Kit Textures folder exists and is not empty, check that the kit textures' filenames and type are correct
def kittextures_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Kit Textures")

    # Check if the folder exists
    if not os.path.isdir(itemfolder_path):
        return

    # If the folder is empty, delete it
    if not os.listdir(itemfolder_path):
        shutil.rmtree(itemfolder_path)
        return

    file_error_tex_format = False
    file_error_names = False
    file_error_any = False

    # Check every texture
    for file_name in os.listdir(itemfolder_path):
        file_path = os.path.join(itemfolder_path, file_name)

        file_error_tex_format = texture_check(file_path)

        if file_error_tex_format:
            break

    # If the folder has a non-dds texture
    if file_error_tex_format:

        # Skip the whole Kit Textures folder
        shutil.rmtree(itemfolder_path)

        # Log the issue
        logging.error( "-")
        logging.error( "- ERROR - Bad kit textures")
        logging.error(f"- Team name:      {team_name}")
        logging.error( "- The Kit Textures folder will be discarded since it's unusable")

        if pause_allow:
            print("-")
            pause()

        return

    # For every texture
    for file_name in os.listdir(itemfolder_path):

        # Check that its name starts with u and that its name has p or g in the correct position
        if not (file_name[0] == 'u' and (file_name[5] == 'p' or file_name[5] == 'g')):

            # Warn about the team having bad texture names
            if not file_error_any:
                logging.error( "-")
                logging.error( "- ERROR - Bad kit texture names")
                logging.error(f"- Team name:      {team_name}")
                file_error_names = True
                file_error_any = True

            logging.error(f"- Texture name:   {file_name}")

            # And skip it
            file_path = os.path.join(itemfolder_path, file_name)
            os.remove(file_path)

    # If the team has bad files close the previously opened message
    if file_error_any:

        logging.error( "- The kit textures mentioned above will be discarded since they're unusable")
        if file_error_names:
            logging.error( "- Check the AET wikipage for the proper naming convention")

        if pause_allow:
            print("-")
            pause()


# If a Logo folder exists and is not empty, check that the three logo images' filenames are correct
def logo_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Logo")

    # Check if the folder exists
    if not os.path.isdir(itemfolder_path):
        return

    # If the folder is empty, delete it
    if not os.listdir(itemfolder_path):
        shutil.rmtree(itemfolder_path)
        return

    # Initialize the variables
    file_error = False
    file_count = 0
    file_good_count = 0

    # For every image
    for file_name in os.listdir(itemfolder_path):

        # Check that its name starts with emblem_
        file_error = not file_name.lower().startswith("emblem_")

        # Check the suffix and increase the plus counter if present and correct
        if (file_name.lower().endswith(("_r.png", "_r_l.png", "_r_ll.png"))):
            file_good_count += 1

        file_count += 1

        if file_error:
            break

    # Check that there are three total images and they all have the correct suffix
    if (file_count != 3) or (file_good_count != 3):
        file_error = True

    # If something's wrong
    if file_error:

        # Skip the whole folder
        shutil.rmtree(itemfolder_path)

        # Log the issue
        logging.error( "-")
        logging.error( "- ERROR - Wrong logo filenames")
        logging.error(f"- Team name:      {team_name}")
        logging.error( "- The Logo folder will be discarded since it's unusable")
        logging.error( "- Check the AET wikipage for the proper naming convention")

        if pause_allow:
            print("-")
            pause()


# If a Portraits folder exists and is not empty, check that the portraits' filenames are correct
def portraits_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Portraits")

    # Check if the folder exists
    if not os.path.isdir(itemfolder_path):
        return

    # If the folder is empty, delete it
    if not os.listdir(itemfolder_path):
        shutil.rmtree(itemfolder_path)
        return

    file_error_any = False

    for file_name in os.listdir(itemfolder_path):

        file_error = False
        file_error_prefix = True
        file_error_id = True

        # Check that the player number starts with "player_" and is within the 01-23 range
        file_error_prefix = not (file_name[:7] == "player_")
        file_error_id = not (file_name[-6:-4].isdigit() and '01' <= file_name[-6:-4] <= '23')

        # Check that the texture is proper
        file_path = os.path.join(itemfolder_path, file_name)
        file_error_tex_format = texture_check(file_path)

        # Set the main flag if any of the checks failed
        file_error = (
            file_error_prefix or
            file_error_id or
            file_error_tex_format
        )

        # If the file is bad
        if file_error:
            if not file_error_any:
                file_error_any = True
                logging.error( "-")
                logging.error( "- ERROR - Bad portrait")
                logging.error(f"- Team name:      {team_name}")

            # Give an error depending on the particular problem
            logging.error(f"- Portrait name:  {file_name} ")

            if file_error_prefix:
                logging.error( "- (incorrect prefix, should be \"player_\")")
            if file_error_id:
                logging.error(f"- (player number {file_name[-6:-4]} out of the 01-23 range)")
            if file_error_tex_format:
                logging.error( "- (bad format)")

            # And skip it
            os.remove(os.path.join(itemfolder_path, file_name))

    # If the team has bad files close the previously opened message
    if file_error_any:

        logging.error( "- These portraits will be discarded since they're unusable")

        if pause_allow:
            print("-")
            pause()


# If a Common folder exists and is not empty, check that the textures inside are fine
def common_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Common")

    # Check if the folder exists
    if not os.path.isdir(itemfolder_path):
        return

    # If the folder is empty, delete it
    if not os.listdir(itemfolder_path):
        shutil.rmtree(itemfolder_path)
        return

    file_error_any = False

    # Check every texture
    for file_name in os.listdir(itemfolder_path):
        file_path = os.path.join(itemfolder_path, file_name)

        file_error_tex_format = texture_check(file_path)

        # If the file has something wrong
        if file_error_tex_format:

            # Warn about the team having bad common textures
            if not file_error_any:
                file_error_any = True
                logging.error( "-")
                logging.error( "- ERROR - Bad common textures")
                logging.error(f"- Team name:      {team_name}")

            logging.error(f"- Texture name:   {file_name}")

            # And skip it
            os.remove(os.path.join(itemfolder_path, file_name))

    # If the team has bad common textures close the previously opened message
    if file_error_any:

        logging.error( "- The textures mentioned above will be discarded since they're unusable")

        if pause_allow:
            print("-")
            pause()


# If a Boots folder exists and is not empty, check that the boots folder names are correct
def boots_check(exportfolder_path, team_name, team_id):
    itemfolder_path = os.path.join(exportfolder_path, "Boots")

    # Check if the folder exists
    if not os.path.isdir(itemfolder_path):
        return

    # If the folder is empty, delete it
    if not os.listdir(itemfolder_path):
        shutil.rmtree(itemfolder_path)
        return

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    strict_file_type_check = int(os.environ.get('FILETYPE_CHECK_STRICT', '1'))

    MODEL_ALLOWED_LIST = [
        "boots.model",
        "boots_edit.model",
    ]

    folder_error_any = None
    folder_num_list = []

    # Prepare a list of subfolders
    subfolder_list = [subfolder for subfolder in os.listdir(itemfolder_path) if os.path.isdir(os.path.join(itemfolder_path, subfolder))]

    # For every subfolder
    for subfolder_name in subfolder_list:

        subfolder_path = os.path.join(itemfolder_path, subfolder_name)

        # Initialize error subflags
        folder_error_name = False
        folder_error_num_repeated = False
        folder_error_model_disallowed_list = []
        folder_error_tex_format = False
        folder_error_mtl_format = False
        folder_error_file_disallowed_list = []

        # Check that its name starts with a k and that the 4 characters after it are digits
        folder_num = subfolder_name[1:5]
        folder_error_name = not (subfolder_name.startswith('k') and folder_num.isdigit())

        # Check that the number is not repeated
        if folder_num in folder_num_list:
            folder_error_num_repeated = True

        folder_num_list.append(folder_num)

        if not fox_mode:
            # If there's no xml, check that all of the .model files are allowed
            model_files = [file for file in os.listdir(subfolder_path) if file.endswith('.model')]
            for model_file in model_files:
                if model_file not in MODEL_ALLOWED_LIST:
                    folder_error_model_disallowed_list.append(model_file)

        # Check every texture
        for file_name in os.listdir(subfolder_path):
            file_path = os.path.join(subfolder_path, file_name)

            folder_error_tex_format = texture_check(file_path)

            if folder_error_tex_format:
                break

        # Check every mtl file
        if not fox_mode:
            for mtl_name in [f for f in os.listdir(subfolder_path) if f.endswith(".mtl")]:
                mtl_path = os.path.join(subfolder_path, mtl_name)

                if mtl_check(mtl_path, team_id):
                    folder_error_mtl_format = True

        # Make a list with the allowed and disallowed file types
        file_type_disallowed_list = PREFOX_FILE_TYPE_DISALLOWED_LIST if not fox_mode else FOX_FILE_TYPE_DISALLOWED_LIST
        file_type_allowed_list_filtered = [
            file_type for file_type in FILE_TYPE_ALLOWED_LIST if file_type not in file_type_disallowed_list
        ]
        # Check if any file is disallowed
        for file_name in [f for f in os.listdir(subfolder_path) if os.path.isfile(os.path.join(subfolder_path, f))]:
            file_type = os.path.splitext(file_name)[1].lower()
            if file_type not in file_type_allowed_list_filtered:
                folder_error_file_disallowed_list.append(file_name)

        if folder_error_file_disallowed_list:
            # Determine log level based on the parameter
            if strict_file_type_check:
                log_level = logging.ERROR
                level_text = "ERROR"
                action_text = "This folder will be discarded"
            else:
                log_level = logging.INFO
                level_text = "Info"
                action_text = "Consider removing these files for better compatibility"

            allowed_file_types = ", ".join(file_type_allowed_list_filtered)

            logging.log(log_level, "-")
            logging.log(log_level, f"- {level_text} - Disallowed files")
            logging.log(log_level, f"- Team name:          {team_name}")
            logging.log(log_level, f"- Boots folder:       {subfolder_name}")
            for file_name in folder_error_file_disallowed_list:
                logging.log(log_level, f"- File name:          {file_name}")
            logging.log(log_level, f"- Allowed file types: {allowed_file_types}")
            logging.log(log_level, "-")
            logging.log(log_level, f"- {action_text}")

            # If strict file type check is disabled, clear the list
            if not strict_file_type_check:
                folder_error_file_disallowed_list = []

        # Set the main flag if any of the checks failed
        folder_error = any((
            folder_error_name,
            folder_error_num_repeated,
            folder_error_model_disallowed_list,
            folder_error_tex_format,
            folder_error_mtl_format,
            folder_error_file_disallowed_list,
        ))

        # If the folder has something wrong
        if folder_error:

            # Warn about the team having bad folders
            if not folder_error_any:
                folder_error_any = True
                logging.error( "-")
                logging.error( "- ERROR - Bad boots folders" )
                logging.error(f"- Team name:      {team_name}")

            logging.error(f"- Folder:   {subfolder_name}")

            # Give an error depending on the particular problem
            if folder_error_name:
                logging.error( "- (wrong folder name, must start with k####)")
            if folder_error_num_repeated:
                logging.error(f"- (folder number {subfolder_name[1:5]} already in use)")
            if folder_error_model_disallowed_list:
                for model_name in folder_error_model_disallowed_list:
                    logging.error(f"- ({model_name} is not allowed)")
            if folder_error_tex_format:
                logging.error(f"- ({file_name} is a bad texture)")
            if folder_error_mtl_format:
                logging.error( "- (broken mtl files)")
            if folder_error_file_disallowed_list:
                for file_name in folder_error_file_disallowed_list:
                    logging.error(f"- ({file_name} is not allowed)")

            # And skip it
            shutil.rmtree(subfolder_path)

    # If there were any bad folders
    if folder_error_any:

        logging.error( "- The boots folders mentioned above will be discarded since they're unusable")

        if pause_allow:
            print("-")
            pause()


# If a Gloves folder exists and is not empty, check that the boots folder names are correct
def gloves_check(exportfolder_path, team_name, team_id):
    itemfolder_path = os.path.join(exportfolder_path, "Gloves")

    # Check if the folder exists
    if not os.path.isdir(itemfolder_path):
        return

    # If the folder is empty, delete it
    if not os.listdir(itemfolder_path):
        shutil.rmtree(itemfolder_path)
        return

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    strict_file_type_check = int(os.environ.get('STRICT_FILE_TYPE_CHECK', '1'))

    MODEL_ALLOWED_LIST = [
        "glove_l.model",
        "glove_r.model",
        "glove_edit.model",
    ]

    folder_error_any = None
    folder_num_list = []

    # Prepare a list of subfolders
    subfolder_list = [subfolder for subfolder in os.listdir(itemfolder_path) if os.path.isdir(os.path.join(itemfolder_path, subfolder))]

    # For every subfolder
    for subfolder_name in subfolder_list:

        subfolder_path = os.path.join(itemfolder_path, subfolder_name)

        # Initialize error subflags
        folder_error_name = False
        folder_error_num_repeated = False
        folder_error_xml_format = False
        folder_error_model_disallowed_list = []
        folder_error_tex_format = False
        folder_error_mtl_format = False
        folder_error_file_disallowed_list = []

        # Check that its name starts with a g and that the 4 characters after it are digits
        folder_num = subfolder_name[1:5]
        folder_error_name = not (subfolder_name.startswith('g') and folder_num.isdigit())

        # Check that the number is not repeated
        if folder_num in folder_num_list:
            folder_error_num_repeated = True

        folder_num_list.append(folder_num)

        if not fox_mode:
            # Check if the folder has an xml
            glove_xml_path = os.path.join(subfolder_path, "glove.xml")
            if os.path.isfile(glove_xml_path):
                folder_error_xml_format = xml_check(glove_xml_path, team_id)
            else:
                # If there's no xml, check that all of the .model files are allowed
                model_files = [file for file in os.listdir(subfolder_path) if file.endswith('.model')]
                for model_file in model_files:
                    if model_file not in MODEL_ALLOWED_LIST:
                        folder_error_model_disallowed_list.append(model_file)

        # Check every texture
        for file_name in os.listdir(subfolder_path):
            file_path = os.path.join(subfolder_path, file_name)

            folder_error_tex_format = texture_check(file_path)

            if folder_error_tex_format:
                break

        # Check every mtl file
        if not fox_mode:
            for mtl_name in [f for f in os.listdir(subfolder_path) if f.endswith(".mtl")]:
                mtl_path = os.path.join(subfolder_path, mtl_name)

                if mtl_check(mtl_path, team_id):
                    folder_error_mtl_format = True

        # Make a list with the allowed and disallowed file types
        file_type_disallowed_list = PREFOX_FILE_TYPE_DISALLOWED_LIST if not fox_mode else FOX_FILE_TYPE_DISALLOWED_LIST
        file_type_allowed_list_filtered = [
            file_type for file_type in FILE_TYPE_ALLOWED_LIST if file_type not in file_type_disallowed_list
        ]
        # Check if any file is disallowed
        for file_name in [f for f in os.listdir(subfolder_path) if os.path.isfile(os.path.join(subfolder_path, f))]:
            file_type = os.path.splitext(file_name)[1].lower()
            if file_type not in file_type_allowed_list_filtered:
                folder_error_file_disallowed_list.append(file_name)

        if folder_error_file_disallowed_list:
            # Determine log level based on the parameter
            if strict_file_type_check:
                log_level = logging.ERROR
                level_text = "ERROR"
                action_text = "This folder will be discarded"
            else:
                log_level = logging.INFO
                level_text = "Info"
                action_text = "Consider removing these files for better compatibility"

            allowed_file_types = ", ".join(file_type_allowed_list_filtered)

            logging.log(log_level, "-")
            logging.log(log_level, f"- {level_text} - Disallowed files")
            logging.log(log_level, f"- Team name:          {team_name}")
            logging.log(log_level, f"- Gloves folder:      {subfolder_name}")
            for file_name in folder_error_file_disallowed_list:
                logging.log(log_level, f"- File name:          {file_name}")
            logging.log(log_level, f"- Allowed file types: {allowed_file_types}")
            logging.log(log_level, "-")
            logging.log(log_level, f"- {action_text}")

            # If strict file type check is disabled, clear the list
            if not strict_file_type_check:
                folder_error_file_disallowed_list = []

        # Set the main flag if any of the checks failed
        folder_error = any((
            folder_error_name,
            folder_error_num_repeated,
            folder_error_xml_format,
            folder_error_model_disallowed_list,
            folder_error_tex_format,
            folder_error_mtl_format,
            folder_error_file_disallowed_list,
        ))

        # If the folder has something wrong
        if folder_error:

            # Warn about the team having bad folders
            if not folder_error_any:
                folder_error_any = True
                logging.error( "-")
                logging.error( "- ERROR - Bad gloves folders")
                logging.error(f"- Team name:      {team_name}")

            logging.error(f"- Folder:   {subfolder_name}")

            # Give an error depending on the particular problem
            if folder_error_name:
                logging.error( "- (wrong folder name, must start with g####)")
            if folder_error_num_repeated:
                logging.error(f"- (folder number {subfolder_name[1:5]} already in use)")
            if folder_error_xml_format:
                logging.error( "- (broken xml file)")
            if folder_error_model_disallowed_list:
                for model_name in folder_error_model_disallowed_list:
                    logging.error(f"- ({model_name} is not allowed)")
            if folder_error_tex_format:
                logging.error(f"- ({file_name} is a bad texture)")
            if folder_error_mtl_format:
                logging.error( "- (broken mtl files)")
            if folder_error_file_disallowed_list:
                for file_name in folder_error_file_disallowed_list:
                    logging.error(f"- ({file_name} is not allowed)")

            # And skip it
            shutil.rmtree(subfolder_path)

    # If there were any bad folders
    if folder_error_any:

        logging.error( "- The gloves folders mentioned above will be discarded since they're unusable")

        if pause_allow:
            print("-")
            pause()


# If an Other folder exists, check that it's not empty
def other_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Other")

    # Check if the folder exists
    if not os.path.isdir(itemfolder_path):
        return

    # If the folder is empty, delete it
    if not os.listdir(itemfolder_path):
        shutil.rmtree(itemfolder_path)
        return


# Function with all the checks
def export_check(exportfolder_path, team_name, team_id):

    # Read the necessary parameters
    global fox_mode, fox_19, fox_21, pause_allow
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    fox_19 = (int(os.environ.get('PES_VERSION', '19')) >= 19)
    fox_21 = (int(os.environ.get('PES_VERSION', '19')) >= 21)
    pause_allow = int(os.environ.get('PAUSE_ALLOW', '1'))

    nested_folders_fix(exportfolder_path, team_name)
    faces_check(exportfolder_path, team_name, team_id)
    kitconfigs_check(exportfolder_path, team_name)
    kittextures_check(exportfolder_path, team_name)
    logo_check(exportfolder_path, team_name)
    portraits_check(exportfolder_path, team_name)
    common_check(exportfolder_path, team_name)
    boots_check(exportfolder_path, team_name, team_id)
    gloves_check(exportfolder_path, team_name, team_id)
    other_check(exportfolder_path, team_name)
