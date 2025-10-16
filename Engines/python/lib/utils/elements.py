import os
import shutil
import xml.etree.ElementTree as ET

from .file_management import file_critical_check
from .FILE_INFO import (
    TEMPLATE_FOLDER_PATH,
    DUMMY_MODEL_NAME,
    DUMMY_MTL_NAME,
)


def dummy_element(folder_path):

    DUMMY_MODEL_PATH = os.path.join(TEMPLATE_FOLDER_PATH, DUMMY_MODEL_NAME)
    DUMMY_MTL_PATH = os.path.join(TEMPLATE_FOLDER_PATH, DUMMY_MTL_NAME)

    dummy_model_destination = os.path.join(folder_path, DUMMY_MODEL_NAME)
    if not os.path.isfile(dummy_model_destination):
        file_critical_check(DUMMY_MODEL_PATH)
        # Copy the oral_dummy_win32.model file from the templates folder to the xml folder
        shutil.copyfile(DUMMY_MODEL_PATH, dummy_model_destination)

    dummy_model_path_xml = f"./{DUMMY_MODEL_NAME.replace('win32', '*')}"

    dummy_mtl_destination = os.path.join(folder_path, DUMMY_MTL_NAME)
    if not os.path.isfile(dummy_mtl_destination):
        file_critical_check(DUMMY_MTL_PATH)
        # Copy the dummy.mtl file from the templates folder to the xml folder
        shutil.copyfile(DUMMY_MTL_PATH, dummy_mtl_destination)

    dummy_mtl_path_xml = f"./{DUMMY_MTL_NAME}"

    # Add a model entry to the .xml file, with the type "face_neck" and the first mtl path from the list
    dummy_model = ET.Element('model')
    dummy_model.set('level', '0')
    dummy_model.set('type', 'face_neck')
    dummy_model.set('path', dummy_model_path_xml)
    dummy_model.set('material', dummy_mtl_path_xml)

    return dummy_model


def glove_element(folder_path, glove_side):

    MTL_DEFAULT_NAME = "materials.mtl"

    glove_name = f"glove_{glove_side}.model"
    glove_path = os.path.join(folder_path, glove_name)

    if not os.path.isfile(glove_path):
        return None

    glove_type = f"glove{glove_side.upper()}"
    glove_path_xml = f"./{glove_name}"

    mtl_test_name = glove_name.replace('.model', '.mtl')
    mtl_test_path = os.path.join(folder_path, mtl_test_name)

    if os.path.isfile(mtl_test_path):
        mtl_path_xml = f"./{mtl_test_name}"
    else:
        mtl_path_xml = f"./{MTL_DEFAULT_NAME}"

    # Add a model entry to the root
    model = ET.Element('model')
    model.set('level', '0')
    model.set('type', glove_type)
    model.set('path', glove_path_xml)
    model.set('material', mtl_path_xml)

    return model
