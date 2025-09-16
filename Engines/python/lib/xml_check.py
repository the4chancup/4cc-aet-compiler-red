import os
import re
import logging
import xml.etree.ElementTree as ET
import xml.parsers.expat

from .cpk_tools import files_fetch_from_cpks
from .utils.zlib_plus import unzlib_file
from .utils.elements import dummy_element
from .utils.id_change import path_id_change
from .utils.pausing import pause


def type_string_get(listed_file_type):
    type_string_raw = f"{listed_file_type} path:"
    type_string = type_string_raw + " " * (16 - len(type_string_raw))
    return type_string


def file_exists(file_path):
    """
    Check if the filename contains the u0XXXp or u0XXXg pattern.
    If it does, search for a u0XXXp1 or u0XXXg1 file in the folder where the file should be.
    If it doesn't, check if the file exists.

    Parameters:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file exists, False otherwise.
    """

    file_name = os.path.basename(file_path)
    file_folder = os.path.dirname(file_path)

    # Make sure the folder where the file should be exists
    if not os.path.exists(file_folder):
        return False

    # Check if the filename contains the u0XXXp pattern
    if re.search(r'u0[a-zA-Z0-9]{3}p', file_name):

        # Search for a u0XXXp1 file in the folder where the file should be
        for file in os.listdir(file_folder):
            if re.search(r'u0[a-zA-Z0-9]{3}p1', file):
                return True
        return False

    # Check if the filename contains the u0XXXg pattern
    elif re.search(r'u0[a-zA-Z0-9]{3}g', file_name):

        # Search for a u0XXXg1 file in the folder where the file should be
        for file in os.listdir(file_folder):
            if re.search(r'u0[a-zA-Z0-9]{3}g1', file):
                return True
        return False

    else:
        return (os.path.exists(file_path))


def listed_file_check(xml_path, xml_name, xml_folder_name, listed_file_path, listed_file_type, team_id, material_name=None, sampler_name=None):

    # Read the necessary parameters
    pes_version = os.environ.get('PES_VERSION', '19')

    UNIFORM_COMMON_PATH = 'model/character/uniform/common/'
    UNIFORM_COMMON_PATH_LENGTH = len(UNIFORM_COMMON_PATH)
    UNIFORM_COMMON_PATH_WITH_ID_LENGTH = UNIFORM_COMMON_PATH_LENGTH + 4
    FACE_COMMON_PATH = 'model/character/face/common/'

    FILE_NAME_EXCEPTION_LIST = [
        'dummy_kit.dds',
        'dummy_gk_kit.dds',
    ]

    # Get the extension of the xml file
    xml_extension = os.path.splitext(xml_path)[1][1:].upper()

    if not listed_file_path:
        logging.error( "-")
        logging.error(f"- ERROR - Missing {listed_file_type.lower()} path")
        logging.error(f"- Folder:         {xml_folder_name}")
        logging.error(f"- {xml_extension} name:       {xml_name}")
        if listed_file_type == "Texture":
            logging.error(f"- Material:       {material_name}")
            logging.error(f"- Sampler:        {sampler_name}")

        return True

    # Check if the filename is in the list of exceptions
    if os.path.basename(listed_file_path) in FILE_NAME_EXCEPTION_LIST:
        return False

    file_path_short = None

    # Check if the file path is a relative path and the file exists in the path indicated
    if listed_file_path.startswith('./'):

        # Remove the "./" from the path
        file_subpath = listed_file_path[2:]
        file_path = os.path.join(os.path.dirname(xml_path), file_subpath)

        # Replace * in the path with "win32"
        file_path_real = file_path.replace('*', 'win32')

        if file_exists(file_path_real):
            return False

    # Check if the file path points to the uniform common folder
    elif listed_file_path.startswith(UNIFORM_COMMON_PATH):

        # Check if the file path contains any further subfolders
        if '/' not in listed_file_path[UNIFORM_COMMON_PATH_LENGTH:]:
            return False

        # Check for a three character folder in the common folder path
        if not re.search(r'/[a-zA-Z0-9]{3}/', listed_file_path[:UNIFORM_COMMON_PATH_WITH_ID_LENGTH], flags=re.IGNORECASE):
            type_string = type_string_get(listed_file_type)
            logging.error( "-")
            logging.error( "- ERROR - Files loaded from the Common folder must use a path with")
            logging.error( "          a subfolder whose name is three characters long (e.g. /XXX/)")
            logging.error(f"- Folder:         {xml_folder_name}")
            logging.error(f"- {xml_extension} name:       {xml_name}")
            logging.error(f"- {type_string}{listed_file_path}")

            return True

        # If the PES version is 16 and the file is a model file, throw an error
        if pes_version == 16 and listed_file_type == "Model":
            logging.error( "-")
            logging.error(f"- ERROR - {listed_file_type} files cannot be loaded from the Common folder on PES16")
            logging.error(f"- Folder:         {xml_folder_name}")
            logging.error(f"- {xml_extension} name:       {xml_name}")
            logging.error(f"- Model path:     {listed_file_path}")

            return True

        # Remove the "model/character/uniform/common/XXX/" section from the path
        file_subpath = listed_file_path[UNIFORM_COMMON_PATH_WITH_ID_LENGTH:]
        common_folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(xml_path))), "Common")
        file_path = os.path.join(common_folder_path, file_subpath)

        # Replace * in the path with "win32"
        file_path_real = file_path.replace('*', 'win32')

        if file_exists(file_path_real):
            return False

        # Search for the file in every midcup cpk and the faces cpk in the download folder
        listed_file_path_real = "common/character1/" + path_id_change(listed_file_path, team_id).replace('p0', 'p1')
        file_info_list = [
            {'source_path': listed_file_path_real},
        ]
        cpk_names_list = ['midcup', 'uniform', 'faces']

        if files_fetch_from_cpks(file_info_list, cpk_names_list, fetch=False):
            return False

    # Check if the file path points to the face common folder
    elif listed_file_path.startswith(FACE_COMMON_PATH):
        return False

    # If the file path is not a relative path nor points to the common folders, it is unusable
    else:
        file_path_short = "Unknown"

    if not file_path_short:
        # Find the path of the extracted folder
        extracted_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(xml_path))))
        # Remove the extracted folder path and / from the path
        extracted_path_length = len(extracted_path)
        file_path_short = file_path[(extracted_path_length+1):]

    ##TODO: Make error-only and merge once the templates have been updated
    type_string = type_string_get(listed_file_type)
    if listed_file_type == "Texture":
        logging.warning( "-")
        logging.warning(f"- Warning - {listed_file_type} file does not exist in the path indicated")
        logging.warning(f"- Folder:         {xml_folder_name}")
        logging.warning(f"- {xml_extension} name:       {xml_name}")
        logging.warning(f"- Material:       {material_name}")
        logging.warning(f"- Sampler:        {sampler_name}")
        logging.warning(f"- {type_string}{listed_file_path}")
        logging.warning(f"- Export path:    {file_path_short}")

        return False

    logging.error( "-")
    logging.error(f"- ERROR - {listed_file_type} file does not exist in the path indicated")
    logging.error(f"- Folder:         {xml_folder_name}")
    logging.error(f"- {xml_extension} name:       {xml_name}")
    logging.error(f"- {type_string}{listed_file_path}")
    logging.error(f"- Export path:    {file_path_short}")

    return True


def face_diff_xml_check(xml_path):
    """
    Checks the given face_diff.xml file.

    Parameters:
        xml_path (str): The path to the .xml file.

    Returns:
        bool: False if the .xml file is valid, True otherwise.
    """

    # Store the name of the file and its parent folder
    xml_name = os.path.basename(xml_path)
    xml_folder_path = os.path.dirname(xml_path)
    xml_folder_name = os.path.basename(xml_folder_path)

    # Try to unzlib the file
    unzlib_file(xml_path)

    # Parse the file
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:

        error_string = xml.parsers.expat.ErrorString(e.code)
        line, column = e.position
        logging.error( "-")
        logging.error( "- ERROR - Invalid .xml file")
        logging.error(f"- Folder:         {xml_folder_name}")
        logging.error(f"- xml name:       {xml_name}")
        logging.error(f"- Issue:          \"{error_string}\"")
        logging.error(f"- Location:       At or before line {line}, column {column}")

        pause()

        return True

    root = tree.getroot()

    # Check that the root tag is 'dif'
    if root.tag != 'dif':
        logging.error( "-")
        logging.error( "- ERROR - Invalid root tag on the second line")
        logging.error(f"- Folder:         {xml_folder_name}")
        logging.error(f"- xml name:       {xml_name}")
        logging.error(f"- Root tag:       <{root.tag}>")
        logging.error( "- Must be:        <dif>")

        pause()

        return True

    return False


def xml_check(xml_path, team_id):
    """
    Checks the given .xml file.

    Parameters:
        xml_path (str): The path to the .xml file.

    Returns:
        bool: False if the .xml file is valid, True otherwise.
    """

    # Store the name of the file and its parent folder
    xml_name = os.path.basename(xml_path)
    xml_folder_path = os.path.dirname(xml_path)
    xml_folder_name = os.path.basename(xml_folder_path)

    # Get the folder type from the name of the xml file
    folder_type = xml_name.split('.')[0]

    # Try to unzlib the file
    unzlib_file(xml_path)

    # Parse the file
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:

        error_string = xml.parsers.expat.ErrorString(e.code)
        line, column = e.position
        logging.error( "-")
        logging.error( "- ERROR - Invalid .xml file")
        logging.error(f"- Folder:         {xml_folder_name}")
        logging.error(f"- xml name:       {xml_name}")
        logging.error(f"- Issue:          \"{error_string}\"")
        logging.error(f"- Location:       At or before line {line}, column {column}")

        pause()

        return True

    root = tree.getroot()

    error = False

    # Check that the root tag is 'config'
    if root.tag != 'config':
        logging.error( "-")
        logging.error( "- ERROR - Invalid root tag on the second line")
        logging.error(f"- Folder:         {xml_folder_name}")
        logging.error(f"- xml name:       {xml_name}")
        logging.error(f"- Root tag:       <{root.tag}>")
        logging.error( "- Must be:        <config>")

        error = True

    model_type_list = []
    model_material_path_list = []

    for model in root.findall('model'):

        model_type = model.get('type')
        model_path = model.get('path')
        model_material_path = model.get('material')

        model_type_error = False

        if not model_type:
            logging.error( "- ERROR - Missing model type")
            logging.error(f"- Folder:         {xml_folder_name}")
            logging.error(f"- xml name:       {xml_name}")
            if model_path:
                logging.error(f"- Model path:     {model_path}")
            logging.error( "-")

            model_type_error = True

        else:
            model_type_list.append(model_type)

        # Check that the model path corresponds to a file in the folder indicated
        model_path_error = listed_file_check(xml_path, xml_name, xml_folder_name, model_path, "Model", team_id)

        # Check that the mtl path corresponds to a file in the folder indicated, if not checked previously
        if (not model_material_path) or (model_material_path not in model_material_path_list):
            model_material_error = listed_file_check(xml_path, xml_name, xml_folder_name, model_material_path, "Mtl", team_id)

            if model_material_path:
                model_material_path_list.append(model_material_path)

        if (
            model_type_error or
            model_path_error or
            model_material_error
        ):
            error = True


    dummy_model = None

    # Check if any of the models has the "face_neck" type
    if folder_type == "face" and ("face_neck" not in model_type_list):

        # Create a dummy model element and add it to the root
        dummy_model = dummy_element(xml_folder_path, model_material_path_list)
        root.append(dummy_model)

        # Create a new root
        root_new = ET.Element('config')

        # Add the original models to the new tree, then the dif block
        for model in root.findall('model'):
            root_new.append(model)
        ET.indent(root_new, '   ')

        for dif in root.findall('dif'):
            root_new.append(dif)

        # Write the modified .xml file
        tree_new = ET.ElementTree(root_new)
        tree_new.write(xml_path, encoding='UTF-8', xml_declaration=True)


    return error


def mtl_check(mtl_path, team_id):
    """
    Checks the given .mtl file.

    Parameters:
        mtl_path (str): The path to the .mtl file.

    Returns:
        bool: False if the .mtl file is valid, True otherwise.
    """

    # Store the name of the file and its parent folder
    mtl_name = os.path.basename(mtl_path)
    mtl_folder_name = os.path.basename(os.path.dirname(mtl_path))

    # Try to unzlib the file
    unzlib_file(mtl_path)

    # Parse the file
    try:
        tree = ET.parse(mtl_path)
    except ET.ParseError as e:

        error_string = xml.parsers.expat.ErrorString(e.code)
        line, column = e.position
        logging.error( "-")
        logging.error( "- ERROR - Invalid .mtl file")
        logging.error(f"- Folder:         {mtl_folder_name}")
        logging.error(f"- MTL name:       {mtl_name}")
        logging.error(f"- Issue:          \"{error_string}\"")
        logging.error(f"- Location:       At or before line {line}, column {column}")

        pause()

        return True

    root = tree.getroot()

    # Create constant list of required state names
    REQUIRED_STATE_NAMES = [
        'alpharef',
        'blendmode',
        'alphablend',
        'alphatest',
        'twosided',
        'ztest',
        'zwrite',
    ]

    error = False

    material_name_list = []

    for material in root.findall('material'):

        # Check if the name of the material is in the list of material names
        material_name = material.get('name')
        error_conflict = (material_name in material_name_list)

        if error_conflict:
            logging.error( "-")
            logging.error( "- ERROR - Material listed more than once")
            logging.error(f"- MTL name:       {mtl_name}")
            logging.error(f"- Material:       \"{material_name}\"")

            error_conflict = True

        # Add the name of the material to the list
        material_name_list.append(material_name)

        if error_conflict:
            error = True
            continue

        # Create dictionary of state names and values
        state_name_dict = {}
        for state in material.findall('state'):
            state_name = state.get('name')
            state_value = state.get('value')
            state_name_dict[state_name] = state_value

            # Check that the value of ztest is 1
            if state_name == 'ztest' and state_value != '1':
                logging.error( "-")
                logging.error( "- ERROR - Value of state \"ztest\" must be 1")
                logging.error(f"- MTL name:       {mtl_name}")
                logging.error(f"- Material:       \"{material_name}\"")
                logging.error(f"- State value:    {state_value}")
                error = True

            # Check that the value of blendmode is 0
            if state_name == 'blendmode' and state_value != '0':
                logging.error( "-")
                logging.error( "- ERROR - Value of state \"blendmode\" must be 0")
                logging.error(f"- MTL name:       {mtl_name}")
                logging.error(f"- Material:       \"{material_name}\"")
                logging.error(f"- State value:    {state_value}")
                error = True

            # Check that the value of alphablend is 0 or 1
            if state_name == 'alphablend' and state_value not in ['0', '1']:
                logging.error( "-")
                logging.error( "- ERROR - Value of state \"alphablend\" must be 0 or 1")
                logging.error(f"- MTL name:       {mtl_name}")
                logging.error(f"- Material:       \"{material_name}\"")
                logging.error(f"- State value:    {state_value}")
                error = True

        # Make a list of state names missing from the list of required state names
        missing_state_names = [state_name for state_name in REQUIRED_STATE_NAMES if state_name not in state_name_dict]

        if missing_state_names:
            ##TODO: Convert to error once the templates have been updated
            ##print("- ERROR - Missing state names")
            logging.warning( "-")
            logging.warning( "- Warning - Missing state names")
            logging.warning(f"- Folder:         {mtl_folder_name}")
            logging.warning(f"- MTL name:       {mtl_name}")
            logging.warning(f"- Material:       \"{material_name}\"")
            # Log the list of missing required state names
            for missing_state_name in missing_state_names:
                logging.warning(f"- State name:     \"{missing_state_name}\"")
            ##error = True

        else:
            warning_nonrecvals = False

            # Check that if the value of alphablend is 1, then the value of alphatest is 0
            if state_name_dict['alphablend'] == '1' and not (state_name_dict['zwrite'] == '0'):
                alphablend_recommended_string = 'recommended 1 if semitransparency is needed, 0 otherwise'
                zwrite_recommended_string = 'recommended 0 if semitransparency is needed, 1 otherwise'

                warning_nonrecvals = True

            # Check that if the value of alphablend is 0, then the value of zwrite is 1
            if state_name_dict['alphablend'] == '0' and not (state_name_dict['zwrite'] == '1'):
                alphablend_recommended_string = 'recommended 0 if semitransparency is not needed, 1 otherwise'
                zwrite_recommended_string = 'recommended 1 if semitransparency is not needed, 0 otherwise'

                warning_nonrecvals = True

            if warning_nonrecvals:
                logging.info( "-")
                logging.info( "- Info - Non-recommended values for states \"alphablend\" and \"zwrite\"")
                logging.info(f"- Folder:         {mtl_folder_name}")
                logging.info(f"- MTL name:       {mtl_name}")
                logging.info(f"- Material:       \"{material_name}\"")
                logging.info(f"- alphablend:     {state_name_dict['alphablend']} ({alphablend_recommended_string})")
                logging.info(f"- zwrite:         {state_name_dict['zwrite']} ({zwrite_recommended_string})")

        # Check, for each sampler, that the texture path corresponds to a texture file in the folder indicated
        for sampler in material.findall('sampler'):

            sampler_name = sampler.get('name')
            sampler_texture_path = sampler.get('path')

            ##TODO: Unify and remove this section once the templates have been updated
            if not sampler_texture_path:
                logging.error( "-")
                logging.error( "- ERROR - Missing texture path")
                logging.error(f"- Folder:         {mtl_folder_name}")
                logging.error(f"- MTL name:       {mtl_name}")
                logging.error(f"- Material:       \"{material_name}\"")
                logging.error(f"- Sampler:        \"{sampler_name}\"")
                error = True
            else:

                texture_path_error = listed_file_check(mtl_path, mtl_name, mtl_folder_name, sampler_texture_path, "Texture", team_id, material_name, sampler_name)

                if texture_path_error:
                    error = True


    return error
