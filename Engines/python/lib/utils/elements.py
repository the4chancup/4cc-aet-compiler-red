import os
import shutil
import xml.etree.ElementTree as ET


def dummy_element(folder_path, mtl_path):

    DUMMY_MODEL_NAME = "oral_dummy_win32.model"

    dummy_model_source = os.path.join('Engines', 'template', DUMMY_MODEL_NAME)
    dummy_model_destination = os.path.join(folder_path, DUMMY_MODEL_NAME)
    dummy_model_path = f"./{DUMMY_MODEL_NAME.replace('win32', '*')}"

    # Copy the oral_dummy_win32.model file from the template folder to the xml folder
    shutil.copyfile(dummy_model_source, dummy_model_destination)

    # Then add a model entry to the .xml file, with the type "face_neck" and the first mtl path from the list
    dummy_model = ET.Element('model')
    dummy_model.set('level', '0')
    dummy_model.set('type', 'face_neck')
    dummy_model.set('path', dummy_model_path)
    dummy_model.set('material', mtl_path)

    return dummy_model
