import os
import copy
import base64
import xml.etree.ElementTree as ET

from .utils.file_management import file_critical_check
from .utils.elements import dummy_element
from .utils.elements import glove_element
from .utils.id_change import txt_id_change


# Global constants
DIFF_NAME = "face_diff"
MODEL_NAME_EXCEPTION_LIST = [
    "hair_high_win32.model",
]
MTL_NAME_DEFAULT = "materials.mtl"
TYPES_LIST = [
    "face_neck",
    "handL",
    "handR",
    "gloveL",
    "gloveR",
    "uniform",
    "shirt",
    "pants_nocloth",
]
TYPE_DEFAULT = "parts"


def diff_data_decode(folder_path, diff_bin_path_default=None):
    """
    Decode diff data from either a bin or xml file.

    Parameters:
        folder_path (str): Path to the folder containing diff files
        diff_bin_path_default (str, optional): Default path for the diff bin file

    Returns:
        ET.Element: The diff element or None if no diff data found
    """
    diff_bin_path_test = os.path.join(folder_path, f"{DIFF_NAME}.bin")
    diff_xml_path = os.path.join(folder_path, f"{DIFF_NAME}.xml")

    if os.path.isfile(diff_bin_path_test):
        diff_bin_path = diff_bin_path_test
        diff_type = "bin"
    elif os.path.isfile(diff_xml_path):
        diff_type = "xml"
    else:
        if diff_bin_path_default:
            diff_bin_path = diff_bin_path_default
            diff_type = "bin"
        else:
            return None

    if diff_type == "xml":
        diff_file = ET.ElementTree(file=diff_xml_path)
        diff_temp = diff_file.getroot()
        diff = copy.deepcopy(diff_temp)
    else:
        diff = ET.Element("dif")
        diff_file = open(diff_bin_path, 'rb').read()
        diff.text = "\n%s\n" % str(base64.b64encode(diff_file), 'utf-8')
        diff.tail = "\n"

    return diff


def xml_create(folder_path, folder_type):

    DIFF_BIN_PATH_DEFAULT = os.path.join("Engines", "templates", f"{DIFF_NAME}.bin")
    file_critical_check(DIFF_BIN_PATH_DEFAULT)

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

            # Check if the model is a face_high model
            if model == "face_high_win32.model":
                model_name_pure = "face_neck"
                model_name = model

            else:
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
                if "model_type_" in model_name_pure:
                    model_type = model_name_pure.split("model_type_")[1].replace(".model", "")
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
            dummy_model = dummy_element(folder_path, model_mtl_path_list)
            root_new.append(dummy_model)

        # Prettify the root
        ET.indent(root_new, '   ')

        # Decode the diff file and add it to the root
        diff = diff_data_decode(folder_path, DIFF_BIN_PATH_DEFAULT)
        if diff is not None:
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


def xml_process(xml_path, team_id):
    """
    Process a face xml file by updating IDs and merging any existing face_diff data.

    Parameters:
        xml_path (str): Path to the face xml file to process
        team_id (str): The team ID to replace in the file
    """
    folder_path = os.path.dirname(xml_path)

    # First run txt_id_change on the xml
    txt_id_change(xml_path, team_id)

    # Search for a new diff block from either bin or xml source
    diff_new = diff_data_decode(folder_path)
    if diff_new is None:
        return

    # Parse the current xml
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Remove any existing diff block
    for diff in root.findall('dif'):
        root.remove(diff)

    # Add the new diff block
    root.append(diff_new)

    # Write back the modified xml
    ET.indent(root, '   ')
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)
