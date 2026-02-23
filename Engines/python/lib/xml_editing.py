import os
import copy
import base64
import xml.etree.ElementTree as ET

from .utils.file_management import file_critical_check
from .utils.elements import dummy_element
from .utils.elements import glove_element
from .utils.name_editing import (
    normalize_kit_dependent_file,
    resolve_link_to_common,
    txt_id_change,
)
from .utils.FILE_INFO import UNIFORM_COMMON_PREFOX_PATH


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
    "eye",
    "mouth",
]
TYPE_DEFAULT = "parts"


def find_mtl_file(main_folder_path, model_folder_path, model_file_name_core):
    """
    Find an appropriate .mtl file for a given model file.

    Parameters:
        main_folder_path (str): Path to the main model folder (e.g. XXX12)
        model_folder_path (str): Path to the directory containing the model file (e.g. XXX12/kit3, common)
        model_file_name_core (str): Core name of the model file (without .model extension)

    Returns:
        tuple: (mtl_file_name, mtl_in_model_folder) where mtl_file_name is the filename
            and mtl_in_model_folder indicates if it's in the model's directory
    """
    def check_mtl_file_name(file_name_raw, model_file_name, match_name=True):
        file_name_resolved_test = resolve_link_to_common(file_name_raw)
        if file_name_resolved_test is not None:
            file_name = file_name_resolved_test.lower()
        else:
            file_name = file_name_raw.lower()
        # Check if the file is an MTL file and if the model name starts with the file name
        if (
            file_name.endswith(".mtl")
        ) and (
            model_file_name.startswith(os.path.splitext(file_name)[0]) or
            not match_name
        ):
            return True
        return False

    # Search in the model's directory first and then in the main model folder
    for search_folder_path, in_model_folder in [(model_folder_path, True), (main_folder_path, False)]:
        file_name_list = [
            f for f in os.listdir(search_folder_path) if
            os.path.isfile(os.path.join(search_folder_path, f))
        ]

        # Find matching .mtl file
        for file_name in file_name_list:
            if check_mtl_file_name(file_name, model_file_name_core):
                return file_name, in_model_folder

        # Find a default .mtl file
        for file_name in file_name_list:
            if check_mtl_file_name(file_name, os.path.splitext(MTL_NAME_DEFAULT)[0]):
                return file_name, in_model_folder

        # Find any .mtl file
        for file_name in file_name_list:
            if check_mtl_file_name(file_name, "", match_name=False):
                return file_name, in_model_folder

    # Fall back to default
    return MTL_NAME_DEFAULT, False


def find_model_files_recursive(folder_path):
    """
    Recursively find all .model files (including .common links) in a folder and its subfolders.

    Parameters:
        folder_path (str): The root folder to search

    Returns:
        list: List of tuples (relative_path, full_path) for each .model file or link found
    """
    model_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Find .model files and .model.common / .model.common.txt links
            if (
                file.lower().endswith(".model") or
                file.lower().endswith(".model.common") or
                file.lower().endswith(".model.common.txt")
            ):
                full_path = os.path.join(root, file)
                # Calculate relative path from folder_path
                rel_path = os.path.relpath(full_path, folder_path)
                model_files.append((rel_path, full_path))
    return model_files


def diff_data_decode(folder_path, diff_bin_path_default=None):
    """
    Decodes diff data from either a bin or xml file then returns the diff element.
    If the file is not default, deletes it.

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
            diff_type = "bin_default"
        else:
            return None

    if diff_type == "xml":
        diff_file = ET.ElementTree(file=diff_xml_path)
        diff_temp = diff_file.getroot()
        diff = copy.deepcopy(diff_temp)
        os.remove(diff_xml_path)
    else:
        diff = ET.Element("dif")
        diff_file = open(diff_bin_path, 'rb').read()
        diff.text = "\n%s\n" % str(base64.b64encode(diff_file), 'utf-8')
        diff.tail = "\n"
        if diff_type != "bin_default":
            os.remove(diff_bin_path)

    return diff


def xml_create(model_folder_path, model_folder_type):

    DIFF_BIN_PATH_DEFAULT = os.path.join("Engines", "templates", f"{DIFF_NAME}.bin")
    file_critical_check(DIFF_BIN_PATH_DEFAULT)

    # Read the necessary parameters
    pes_15 = (int(os.environ.get('PES_VERSION', '19')) == 15)

    # Create a new root
    root_new = ET.Element('config')

    if model_folder_type == "face":

        model_type_list = []
        model_file_path_list = []

        # Recursively find all .model files in the folder and subfolders
        model_files = find_model_files_recursive(model_folder_path)

        for model_rel_path, model_full_path in model_files:

            # Get the filename and directory components
            model_file_name_raw = os.path.basename(model_rel_path)
            model_dir_rel = os.path.dirname(model_rel_path)
            model_dir_full = os.path.dirname(model_full_path)

            # Check if this is a common folder file
            model_file_name_resolved_test = resolve_link_to_common(model_file_name_raw)
            if model_file_name_resolved_test is not None:
                model_file_name = model_file_name_resolved_test.lower()
            else:
                model_file_name = model_file_name_raw.lower()

            # Check if the model filename is in the exception list
            if model_file_name in MODEL_NAME_EXCEPTION_LIST:
                continue

            # Check if the model is a face_high model
            if model_file_name == "face_high_win32.model":
                model_file_name_core = "face_neck"
                model_file_name_full = model_file_name

            # Check if the model filename starts with "oral_" and ends with "_win32"
            elif model_file_name.startswith("oral_") and model_file_name.endswith("_win32.model"):
                model_file_name_core = model_file_name.replace("_win32.model", "").replace("oral_", "")
                model_file_name_full = model_file_name

            else:
                model_file_name_core = model_file_name.replace(".model", "")
                model_file_name_full = "oral_" + model_file_name.replace(".model", "_win32.model")

                if model_file_name_resolved_test is None:
                    # Rename the file if it's not a link
                    new_full_path = os.path.join(model_dir_full, model_file_name_full)
                    os.rename(model_full_path, new_full_path)
                    model_full_path = new_full_path

            # Apply kit normalization to the model name used in XML
            model_file_name_norm = normalize_kit_dependent_file(model_file_name_full)

            # Build the model path for XML
            if model_file_name_resolved_test is not None:
                model_base_path = f"{UNIFORM_COMMON_PREFOX_PATH}XXX/"
            else:
                model_base_path = "./"

            # If the model file is in a subfolder, use the subfolder in the XML
            if model_dir_rel:
                model_dir_xml = model_dir_rel.replace(os.sep, '/') + '/'
            else:
                model_dir_xml = ""

            model_file_name_xml = model_file_name_norm.replace('win32', '*')
            model_file_path_xml = f"{model_base_path}{model_dir_xml}{model_file_name_xml}"

            # Check if the model path was already added to the XML and skip if it was
            if model_file_path_xml in model_file_path_list:
                continue

            model_file_path_list.append(model_file_path_xml)

            mtl_file_name_raw, mtl_in_model_file_dir = (
                find_mtl_file(model_folder_path, model_dir_full, model_file_name_core)
            )

            # Check if the mtl file is a common file
            mtl_file_name_resolved = resolve_link_to_common(mtl_file_name_raw)

            # Build the mtl path for XML
            if mtl_file_name_resolved is not None:
                mtl_base_path = f"{UNIFORM_COMMON_PREFOX_PATH}XXX/"
                mtl_file_name = mtl_file_name_resolved
            else:
                mtl_base_path = "./"
                mtl_file_name = mtl_file_name_raw

            # If the mtl file is in the same directory as the model file, use the model directory
            if mtl_in_model_file_dir:
                mtl_dir_xml = model_dir_xml
            else:
                mtl_dir_xml = ""

            mtl_file_name_xml = mtl_file_name
            mtl_file_path_xml = f"{mtl_base_path}{mtl_dir_xml}{mtl_file_name_xml}"

            # Check if any of the types in the list are in the start of the model name's core
            model_file_name_core_simple = model_file_name_core.replace("_", "")
            for type in TYPES_LIST:
                type_simple = type.replace("_", "").lower()
                if model_file_name_core_simple.startswith(type_simple):
                    model_type = type
                    break
            else:
                # Check if the model name contains "model_type_"
                if "model_type_" in model_file_name_core:
                    # Get the type after "model_type_"
                    model_type = model_file_name_core.split("model_type_")[1]
                else:
                    model_type = TYPE_DEFAULT

            # Replace "uniform" with "uniform_sub" if PES 15
            if pes_15 and model_type == "uniform":
                model_type_xml = "uniform_sub"
            else:
                model_type_xml = model_type

            model_type_list.append(model_type_xml)

            # Add a model entry to the root
            model = ET.Element('model')
            model.set('level', '0')
            model.set('type', model_type_xml)
            model.set('path', model_file_path_xml)
            model.set('material', mtl_file_path_xml)

            # Check if the model name contains "ratio_"
            if "ratio_" in model_file_name_core:
                # Get the ratio after "ratio_"
                ratio = model_file_name_core.split("ratio_")[1]
                # Add ratio attribute
                model.set('ratio', ratio)

            root_new.append(model)

        # Delete all the common file links and any remaining empty subfolders
        for root, dirs, files in os.walk(model_folder_path, topdown=False):
            for file_name in files:
                if ".common" in file_name:
                    os.remove(os.path.join(root, file_name))
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)

        # Check if any of the models has the "face_neck" type
        if "face_neck" not in model_type_list:

            # Create a dummy model element and add it to the root
            dummy_model = dummy_element(model_folder_path)
            root_new.append(dummy_model)

        # Prettify the root
        ET.indent(root_new, '   ')

        # Decode the diff file and add it to the root
        diff = diff_data_decode(model_folder_path, DIFF_BIN_PATH_DEFAULT)
        if diff is not None:
            root_new.append(diff)

    if model_folder_type == "glove":

        # Add the left glove
        glove_l_model = glove_element(model_folder_path, glove_side="l")

        if glove_l_model is not None:
            root_new.append(glove_l_model)

        # Add the right glove
        glove_r_model = glove_element(model_folder_path, glove_side="r")

        if glove_r_model is not None:
            root_new.append(glove_r_model)

        # Prettify the root
        ET.indent(root_new, '   ')


    # Write the modified .xml file
    xml_path = os.path.join(model_folder_path, f"{model_folder_type}.xml")
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


def diff_from_xml(xml_path):
    """
    Extracts the diff block from a face xml file and writes it to face_diff.xml.

    Parameters:
        xml_path (str): Path to the face xml file containing the diff block
    """
    folder_path = os.path.dirname(xml_path)

    # Parse the xml file
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Find the diff block
    diff = root.find('dif')
    if diff is None:
        return

    # Create a new tree with the diff element as root
    diff_copy = copy.deepcopy(diff)

    # Write the diff to face_diff.xml
    diff_xml_path = os.path.join(folder_path, f"{DIFF_NAME}.xml")
    diff_tree = ET.ElementTree(diff_copy)
    diff_tree.write(diff_xml_path, encoding='utf-8', xml_declaration=True)
