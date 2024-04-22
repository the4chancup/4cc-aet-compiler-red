import os
import shutil
import xml.etree.ElementTree as ET


def dummy_element(folder_path, mtl_path_list):

    DUMMY_MODEL_NAME = "oral_dummy_win32.model"
    DUMMY_MTL_NAME_DEFAULT = "dummy.mtl"

    # Copy the oral_dummy_win32.model file from the template folder to the xml folder
    dummy_model_source = os.path.join('Engines', 'template', DUMMY_MODEL_NAME)
    dummy_model_destination = os.path.join(folder_path, DUMMY_MODEL_NAME)
    shutil.copyfile(dummy_model_source, dummy_model_destination)

    dummy_model_path = f"./{DUMMY_MODEL_NAME.replace('win32', '*')}"

    if mtl_path_list:
        dummy_mtl_path = mtl_path_list[0]
    else:
        # Copy the dummy.mtl file from the template folder to the xml folder
        dummy_mtl_source = os.path.join('Engines', 'template', DUMMY_MTL_NAME_DEFAULT)
        dummy_mtl_destination = os.path.join(folder_path, DUMMY_MTL_NAME_DEFAULT)
        shutil.copyfile(dummy_mtl_source, dummy_mtl_destination)

        dummy_mtl_path = f"./{DUMMY_MTL_NAME_DEFAULT}"

    # Then add a model entry to the .xml file, with the type "face_neck" and the first mtl path from the list
    dummy_model = ET.Element('model')
    dummy_model.set('level', '0')
    dummy_model.set('type', 'face_neck')
    dummy_model.set('path', dummy_model_path)
    dummy_model.set('material', dummy_mtl_path)

    return dummy_model


def glove_element(folder_path, glove_side):

    MTL_NAME_DEFAULT = "materials.mtl"

    glove_name = f"glove_{glove_side}.model"
    glove_path = os.path.join(folder_path, glove_name)

    if os.path.isfile(glove_path):

        glove_type = f"glove{glove_side.upper()}"
        glove_path_xml = f"./{glove_name}"

        mtl_name = glove_name.replace('.model', '.mtl')
        mtl_path_xml_test = os.path.join(folder_path, mtl_name)

        if os.path.isfile(mtl_path_xml_test):
            mtl_path_xml = f"./{mtl_name}"
        else:
            mtl_path_xml = f"./{MTL_NAME_DEFAULT}"

        # Add a model entry to the root
        model = ET.Element('model')
        model.set('level', '0')
        model.set('type', glove_type)
        model.set('path', glove_path_xml)
        model.set('material', mtl_path_xml)

        return model

    else:
        return None
