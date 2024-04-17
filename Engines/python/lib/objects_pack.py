import os
import shutil

from . import pes_cpk_pack as cpktool
from . import pes_fpk_pack as fpktool
from .xml_create import xml_create


def objects_packer(object_type, object_source_folder, object_destination_folder, faces_foldername, uniform_foldername):

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)

    object_source_path = os.path.join("extracted_exports", object_source_folder)
    temp_folder_path = os.path.join("temp")

    # Check if the temp folder exists and delete it
    if os.path.exists(temp_folder_path):
        shutil.rmtree(temp_folder_path)

    # Pre-Fox mode
    if not fox_mode:

        # Set the destination path
        if object_type == "face":
            object_destination_path = os.path.join("patches_contents",faces_foldername,"common","character0","model","character","face","real")
        else:
            object_destination_path = os.path.join("patches_contents",uniform_foldername,"common","character0","model","character",object_destination_folder)

        # Create a destination folder if needed
        if not os.path.exists(object_destination_path):
            os.makedirs(object_destination_path)

        # For every folder in the source directory
        for object_name in os.listdir(object_source_path):

            object_id = object_name[:5]
            print(f"- {object_name}")

            object_path = os.path.join(object_source_path, object_name)
            object_path_new = os.path.join(object_source_path, object_id)

            xml_path = os.path.join(object_path, f"{object_id}.xml")
            if not object_type == "boots" and not os.path.exists(xml_path):
                xml_create(object_path, object_type)

            # Rename it with the proper id
            os.rename(object_path, object_path_new)

            if object_type == "face":

                # Make a properly structured temp folder
                temp_path = os.path.join(temp_folder_path, object_id, "common", "character0", "model", "character", "face", "real")
                os.makedirs(temp_path, exist_ok=True)

                # Move the face folder to the temp folder
                shutil.move(object_path_new, temp_path)

                # Make a cpk and put it in the Faces folder
                cpk_source = os.path.join(temp_folder_path, object_id, "common")
                cpk_destination = os.path.join(object_destination_path, f"{object_id}.cpk")
                cpktool.main(cpk_destination, [cpk_source], True)

            else:
                # Delete the old folder if present
                if os.path.exists(os.path.join(object_destination_path, object_id)):
                    shutil.rmtree(os.path.join(object_destination_path, object_id))

                # Move the folder
                shutil.move(object_path_new, object_destination_path)

    # Fox mode
    else:

        # Set the destination path
        object_destination_path = os.path.join("patches_contents", faces_foldername, "Asset", "model", "character", object_destination_folder)

        # Create a destination folder if needed
        if not os.path.exists(object_destination_path):
            os.makedirs(object_destination_path)

        # For every folder in the source directory
        for object_name in os.listdir(object_source_path):

            object_id = object_name[:5]
            print(f"- {object_name}")

            object_path = os.path.join(object_source_path, object_name)
            object_path_new = os.path.join(object_source_path, object_id)

            # Rename it with the proper id
            os.rename(object_path, object_path_new)

            # Delete the old folder if present
            if os.path.exists(os.path.join(object_destination_path, object_id)):
                shutil.rmtree(os.path.join(object_destination_path, object_id))

            # Make a temp folder
            temp_path = os.path.join(temp_folder_path, object_id)
            os.makedirs(os.path.join(temp_path, "#windx11"), exist_ok=True)

            # Move the folder to the temp folder
            shutil.move(object_path_new, temp_path)

            # If the folder has textures
            texture_path = os.path.join(temp_path, object_id)
            if any(file.endswith('.ftex') for file in os.listdir(texture_path)):
                # Move the textures to a separate folder
                for texture_file in os.listdir(texture_path):
                    if texture_file.endswith('.ftex'):
                        shutil.move(os.path.join(texture_path, texture_file),
                                    os.path.join(temp_path, "#windx11"))

            # Move the xml outside
            shutil.move(os.path.join(texture_path, f"{object_type}.fpk.xml"), temp_path)

            # Rename the folder for packing
            os.rename(os.path.join(temp_path, object_id),
                      os.path.join(temp_path, f"{object_type}_fpk"))

            # Pack the fpk
            fpk_destination = os.path.join(temp_path, f"{object_type}.fpk")
            fpk_source_path = os.path.join(temp_path, f"{object_type}_fpk")

            # Prepare an array with the files to pack
            file_path_list = []
            for file_name in os.listdir(fpk_source_path):
                file_path = os.path.join(fpk_source_path, file_name)
                file_path_list.append(file_path)

            # Pack the fpk
            fpktool.main(fpk_destination, file_path_list, True)

            # Make the final folder structure
            final_folder_path = os.path.join(object_destination_path, object_id, "#Win")
            os.makedirs(final_folder_path, exist_ok=True)

            # Move the fpk to the contents folder
            shutil.move(fpk_destination, final_folder_path)

            # Copy the generic fpkd to the same folder and rename it
            generic_fpkd_path = os.path.join("Engines", "generic.fpkd")
            shutil.copy(generic_fpkd_path, final_folder_path)
            os.rename(os.path.join(final_folder_path, "generic.fpkd"),
                      os.path.join(final_folder_path, f"{object_type}.fpkd"))

            # Move the textures
            if object_type == "face":
                source_images_path = os.path.join(object_destination_path, object_id, "sourceimages")
                os.makedirs(source_images_path, exist_ok=True)
                shutil.move(os.path.join(temp_path, "#windx11"), source_images_path)
            else:
                shutil.move(os.path.join(temp_path, "#windx11"),
                            os.path.join(object_destination_path, object_id))

            # Delete the temp folder
            shutil.rmtree(temp_path)

    # Delete the source folder
    if os.path.exists(object_source_path):
        shutil.rmtree(object_source_path)

    # Delete the temp folder
    if os.path.exists(temp_folder_path):
        shutil.rmtree(temp_folder_path)