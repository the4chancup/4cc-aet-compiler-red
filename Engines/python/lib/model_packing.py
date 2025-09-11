import os
import shutil

from . import pes_cpk_pack as cpktool
from . import pes_fpk_pack as fpktool
from .utils.file_management import file_critical_check
from .utils.FILE_INFO import (
    TEMPLATE_FOLDER_PATH,
    GENERIC_FPKD_NAME,
)


def models_pack(models_type, models_source_path, models_destination_folder, cpk_folder_path):

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)

    temp_folder_path = os.path.join("temp")

    # Check if the temp folder exists and delete it
    if os.path.exists(temp_folder_path):
        shutil.rmtree(temp_folder_path)

    # Pre-Fox mode
    if not fox_mode:

        # Set the destination path
        if models_type == "face":
            models_destination_path = os.path.join(cpk_folder_path,"common","character0","model","character","face","real")
        else:
            models_destination_path = os.path.join(cpk_folder_path,"common","character0","model","character",models_destination_folder)

        # Create a destination folder if needed
        if not os.path.exists(models_destination_path):
            os.makedirs(models_destination_path)

        # For every folder in the source directory
        for model_name in os.listdir(models_source_path):

            if models_type == "face" and model_name.startswith("referee"):
                model_id = model_name[:10]
            else:
                model_id = model_name[:5]
            print(f"- {model_name}")

            model_path = os.path.join(models_source_path, model_name)

            if models_type == "face":

                # Make a properly structured temp folder
                temp_path = os.path.join(temp_folder_path, model_id, "common", "character0", "model", "character", "face", "real")
                os.makedirs(temp_path, exist_ok=True)

                # Move the face folder to the temp folder, renaming it to the face ID
                model_temp_path = os.path.join(temp_path, model_id)
                shutil.move(model_path, model_temp_path)

                # Make a cpk and put it in the Faces folder
                cpk_source = os.path.join(temp_folder_path, model_id, "common")
                cpk_destination = os.path.join(models_destination_path, f"{model_id}.cpk")
                cpktool.main(cpk_destination, [cpk_source], True)

            else:
                # Delete the old folder if present
                model_destination_path = os.path.join(models_destination_path, model_id)
                if os.path.exists(model_destination_path):
                    shutil.rmtree(model_destination_path)

                # Move the folder, renaming it to the model ID
                shutil.move(model_path, model_destination_path)

    # Fox mode
    else:

        # Set the destination path
        models_destination_path = os.path.join(cpk_folder_path, "Asset", "model", "character", models_destination_folder)

        # Create a destination folder if needed
        if not os.path.exists(models_destination_path):
            os.makedirs(models_destination_path)

        # Make a list of allowed files
        FILE_TYPE_ALLOWED_LIST = [".bin", ".fmdl", ".skl"]

        # For every folder in the source directory
        for model_name in os.listdir(models_source_path):

            if models_type == "face" and model_name.startswith("referee"):
                model_id = model_name[:10]
            else:
                model_id = model_name[:5]

            print(f"- {model_name}")

            model_path = os.path.join(models_source_path, model_name)

            # Delete the old subfolder if present
            model_destination_path = os.path.join(models_destination_path, model_id)
            if os.path.exists(model_destination_path):
                shutil.rmtree(model_destination_path)

            # Move the model folder to the temp folder, renaming it to the model ID
            temp_path = os.path.join(temp_folder_path, model_id)
            model_temp_path = os.path.join(temp_path, model_id)
            shutil.move(model_path, model_temp_path)

            # Make a "windx11" folder for the textures
            textures_temp_path = os.path.join(temp_path, "#windx11")
            os.makedirs(textures_temp_path, exist_ok=True)

            # If the folder has textures, move them to the windx11 folder
            for texture_file in os.listdir(model_temp_path):
                if texture_file.endswith('.ftex'):
                    shutil.move(os.path.join(model_temp_path, texture_file), textures_temp_path)

            # Delete any folders and any files which aren't on the allowed list
            for item_name in os.listdir(model_temp_path):
                item_path = os.path.join(temp_path, item_name)
                if os.path.isfile(item_path):
                    if os.path.splitext(item_name)[1] not in FILE_TYPE_ALLOWED_LIST:
                        os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

            # Rename the folder for packing
            fpk_source_path = os.path.join(temp_path, f"{models_type}_fpk")
            os.rename(model_temp_path, fpk_source_path)

            # Prepare an array with the files to pack
            file_path_list = []
            for file_name in os.listdir(fpk_source_path):
                file_path = os.path.join(fpk_source_path, file_name)
                file_path_list.append(file_path)

            # Pack the fpk
            fpk_destination_path = os.path.join(temp_path, f"{models_type}.fpk")
            fpktool.main(fpk_destination_path, file_path_list, True)

            # Make the final folder structure
            final_folder_path = os.path.join(models_destination_path, model_id, "#Win")
            os.makedirs(final_folder_path, exist_ok=True)

            # Move the fpk to the contents folder
            shutil.move(fpk_destination_path, final_folder_path)

            # Copy the generic fpkd to the same folder and rename it
            GENERIC_FPKD_PATH = os.path.join(TEMPLATE_FOLDER_PATH, GENERIC_FPKD_NAME)
            fpkd_destination_path = os.path.join(final_folder_path, f"{models_type}.fpkd")
            file_critical_check(GENERIC_FPKD_PATH)
            shutil.copy(GENERIC_FPKD_PATH, fpkd_destination_path)

            # Move the textures
            if models_type == "face":
                source_images_path = os.path.join(models_destination_path, model_id, "sourceimages")
                os.makedirs(source_images_path, exist_ok=True)
                shutil.move(textures_temp_path, source_images_path)
            else:
                shutil.move(textures_temp_path, model_destination_path)

            # Delete the temp folder
            shutil.rmtree(temp_path)

    # Delete the source folder
    if os.path.exists(models_source_path):
        shutil.rmtree(models_source_path)

    # Delete the temp folder
    if os.path.exists(temp_folder_path):
        shutil.rmtree(temp_folder_path)
