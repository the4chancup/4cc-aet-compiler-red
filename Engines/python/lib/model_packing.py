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
            models_destination_path = os.path.join(
                cpk_folder_path,"common","character0","model","character","face","real"
            )
        else:
            models_destination_path = os.path.join(
                cpk_folder_path,"common","character0","model","character",models_destination_folder
            )

        # Create a destination folder if needed
        if not os.path.exists(models_destination_path):
            os.makedirs(models_destination_path)

        # For every folder in the source directory
        for model_folder_name in os.listdir(models_source_path):

            if models_type == "face" and model_folder_name.startswith("referee"):
                model_id = model_folder_name[:10]
            else:
                model_id = model_folder_name[:5]
            print(f"- {model_folder_name}")

            model_folder_path = os.path.join(models_source_path, model_folder_name)

            if models_type == "face":

                # Move the face folder to a properly structured temp folder
                model_temp_folder_path = os.path.join(
                    temp_folder_path, model_id,
                    "common", "character0", "model", "character", "face", "real", model_id
                )
                shutil.move(model_folder_path, model_temp_folder_path)

                # Make a cpk and put it in the Faces folder
                cpk_source = os.path.join(temp_folder_path, model_id, "common")
                cpk_destination = os.path.join(models_destination_path, f"{model_id}.cpk")
                cpktool.main(cpk_destination, [cpk_source], allowOverwrite=True)

            else:
                # Delete the destination folder if present
                model_destination_path = os.path.join(models_destination_path, model_id)
                if os.path.exists(model_destination_path):
                    shutil.rmtree(model_destination_path)

                # Move the model folder, renaming it to the model ID
                shutil.move(model_folder_path, model_destination_path)

    # Fox mode
    else:

        # Set the destination path
        models_destination_path = os.path.join(
            cpk_folder_path, "Asset", "model", "character", models_destination_folder
        )

        # Create a destination folder if needed
        if not os.path.exists(models_destination_path):
            os.makedirs(models_destination_path)

        # Make a list files allowed in the fpk
        FILE_TYPE_ALLOWED_LIST = [".bin", ".fmdl", ".skl"]

        # For every folder in the source directory
        for model_folder_name in os.listdir(models_source_path):

            if models_type == "face" and model_folder_name.startswith("referee"):
                model_id = model_folder_name[:10]
            else:
                model_id = model_folder_name[:5]

            print(f"- {model_folder_name}")

            model_folder_path = os.path.join(models_source_path, model_folder_name)

            # Delete the destination folder if present
            model_destination_path = os.path.join(models_destination_path, model_id)
            if os.path.exists(model_destination_path):
                shutil.rmtree(model_destination_path)

            # Move the model folder to the temp folder, renaming it with the model type
            model_temp_folder_path = os.path.join(temp_folder_path, model_id)
            fpk_temp_folder_path = os.path.join(model_temp_folder_path, f"{models_type}_fpk")
            shutil.move(model_folder_path, fpk_temp_folder_path)

            # Make a #windx11 folder for the other files
            windx_temp_path = os.path.join(model_temp_folder_path, "#windx11")
            os.makedirs(windx_temp_path, exist_ok=True)

            # Move any folders and any files which aren't on the allowed list
            for item_name in os.listdir(fpk_temp_folder_path):
                item_path = os.path.join(fpk_temp_folder_path, item_name)
                if not (
                    os.path.isfile(item_path) and
                    os.path.splitext(item_name)[1] in FILE_TYPE_ALLOWED_LIST
                ):
                    shutil.move(item_path, windx_temp_path)

            # Prepare an array with the files to pack
            file_path_list = []
            for file_name in os.listdir(fpk_temp_folder_path):
                file_path = os.path.join(fpk_temp_folder_path, file_name)
                file_path_list.append(file_path)

            # Pack the fpk
            fpk_temp_path = os.path.join(model_temp_folder_path, f"{models_type}.fpk")
            fpktool.main(fpk_temp_path, file_path_list, True)

            # Make the final folder structure
            model_final_folder_path = os.path.join(models_destination_path, model_id)
            fpk_final_folder_path = os.path.join(model_final_folder_path, "#Win")
            os.makedirs(fpk_final_folder_path, exist_ok=True)

            # Move the fpk to the contents folder
            shutil.move(fpk_temp_path, fpk_final_folder_path)

            # Copy the generic fpkd to the same folder and rename it
            GENERIC_FPKD_PATH = os.path.join(TEMPLATE_FOLDER_PATH, GENERIC_FPKD_NAME)
            file_critical_check(GENERIC_FPKD_PATH)
            fpkd_destination_path = os.path.join(fpk_final_folder_path, f"{models_type}.fpkd")
            shutil.copy(GENERIC_FPKD_PATH, fpkd_destination_path)

            # Move the other files, using sourceimages in the path if it's a face model
            # Keep in mind that model folders do not support loading textures from subfolders
            if models_type == "face":
                windx_final_path = os.path.join(model_final_folder_path, "sourceimages", "#windx11")
            else:
                windx_final_path = os.path.join(model_final_folder_path, "#windx11")

            shutil.move(windx_temp_path, windx_final_path)

            # Delete the temp folder
            shutil.rmtree(model_temp_folder_path)

    # Delete the source folder
    if os.path.exists(models_source_path):
        shutil.rmtree(models_source_path)

    # Delete the main temp folder
    if os.path.exists(temp_folder_path):
        shutil.rmtree(temp_folder_path)
