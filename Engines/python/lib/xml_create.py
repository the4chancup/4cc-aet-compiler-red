import os
import base64
import xml.etree.ElementTree as ET

from .utils.elements import dummy_element
from .utils.elements import glove_element


def xml_create(folder_path, folder_type):

    MODEL_NAME_EXCEPTION_LIST = [
        'hair_high.model',
    ]

    MTL_NAME_DEFAULT = "materials.mtl"

    DIFF_NAME = "face_diff.bin"
    DIFF_PATH_DEFAULT = os.path.join("Engines", "template", DIFF_NAME)

    TYPES_LIST = [
        "face_neck",
        "handL",
        "handR",
        "gloveL",
        "gloveR",
        "uniform",
    ]
    TYPE_DEFAULT = "parts"


    # Create a new root
    root_new = ET.Element('config')

    if folder_type == "face":

        model_type_list = []
        model_mtl_path_list = []

        # For each .model file in the folder
        for model in [f for f in os.listdir(folder_path) if f.endswith(".model")]:

            # Check if the model filename is in the exception list
            if model in MODEL_NAME_EXCEPTION_LIST:
                continue

            # Check if the model filename starts with "oral_" and ends with "_win32"
            if model.startswith("oral_") and model.endswith("_win32.model"):
                model_name_pure = model.replace("_win32.model", "").replace("oral_", "")
                model_name = model
            else:
                model_name_pure = model
                model_name = "oral_" + model.replace(".model", "_win32.model")
                os.rename(os.path.join(folder_path, model), os.path.join(folder_path, model_name))

            model_path_xml = f"./{model_name.replace('win32', '*')}"

            # Check if any .mtl files in the folder have a name matching the start of the pure model name
            for mtl in [f for f in os.listdir(folder_path) if f.endswith(".mtl")]:
                if model_name_pure.startswith(os.path.splitext(mtl)[0]):
                    mtl_name = mtl
                    break
            else:
                mtl_name = MTL_NAME_DEFAULT

            mtl_path_xml = f"./{mtl_name}"
            model_mtl_path_list.append(mtl_path_xml)

            # Check if any of the types in the list are in the start of the pure model name
            model_name_pure_simple = model_name_pure.replace("_", "").lower()
            for type in TYPES_LIST:
                type_simple = type.replace("_", "").lower()
                if model_name_pure_simple.startswith(type_simple):
                    model_type = type
                    break
            else:
                model_type = TYPE_DEFAULT

            model_type_list.append(model_type)

            # Add a model entry to the root
            model = ET.Element('model')
            model.set('level', '0')
            model.set('type', model_type)
            model.set('path', model_path_xml)
            model.set('material', mtl_path_xml)

            root_new.append(model)

        # Check if any of the models has the "face_neck" type
        if "face_neck" not in model_type_list:

            # Create a dummy model element and add it to the root
            dummy_model = dummy_element(folder_path, model_mtl_path_list[0])
            root_new.append(dummy_model)

        # Prettify the root
        ET.indent(root_new, '   ')

        # Decode the diff file and add it to the root
        diff = ET.Element("dif")

        diff_path_test = os.path.join(folder_path, DIFF_NAME)
        if os.path.isfile(diff_path_test):
            diff_path = diff_path_test
        else:
            diff_path = DIFF_PATH_DEFAULT

        diff_file = open(diff_path, 'rb').read()
        diff.text = "\n%s\n" % str(base64.b64encode(diff_file), 'utf-8')
        diff.tail = "\n"
        root_new.append(diff)

    if folder_type == "glove":

        # Add the left glove
        glove_l_model = glove_element(folder_path, glove_side="l")

        if glove_l_model is not None:
            root_new.append(glove_l_model)

        # Add the right glove
        glove_r_model = glove_element(folder_path, glove_side="r")

        if glove_r_model is not None:
            root_new.append(glove_r_model)

        # Prettify the root
        ET.indent(root_new, '   ')


    # Write the modified .xml file
    xml_path = os.path.join(folder_path, f"{folder_type}.xml")
    tree_new = ET.ElementTree(root_new)
    tree_new.write(xml_path, encoding='UTF-8', xml_declaration=True)

    return
