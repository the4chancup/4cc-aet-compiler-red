import os
import re
import xml.etree.ElementTree as ET

from .utils.zlib_plus import unzlib_file
from .utils.elements import dummy_element


# Read the necessary parameters
global pes_version
pes_version = int(os.environ.get('PES_VERSION', '16'))


def file_exists(file_path):
    """
    Check if the filename contains the u0XXXp pattern.
    If it does, search for a u0XXXp1 file in the folder where the file should be.
    If it doesn't, check if the file exists.

    Parameters:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file exists, False otherwise.
    """

    # Check if the filename contains the u0XXXp pattern
    if not re.search(r'u0[a-zA-Z0-9]{3}p', os.path.basename(file_path)):

        return (os.path.exists(file_path))

    else:
        # Search for a u0XXXp1 file in the folder where the file should be
        for file in os.listdir(os.path.dirname(file_path)):
            if re.search(r'u0[a-zA-Z0-9]{3}p1', file):
                return True

        return False


def listed_file_check(xml_path, xml_name, xml_folder_name, listed_file_path, listed_file_type, material_name=None, sampler_name=None):

    FILE_NAME_EXCEPTION_LIST = [
        'dummy_kit.dds',
        'dummy_gk_kit.dds',
    ]

    # Get the extension of the xml file
    xml_extension = os.path.splitext(xml_path)[1][1:].upper()

    error = False

    if not listed_file_path:
        print(f"- ERROR - Missing {listed_file_type.lower()} path")
        print(f"- Folder:         {xml_folder_name}")
        print(f"- {xml_extension} name:       {xml_name}")
        if listed_file_type == "Texture":
            print(f"- Material:       {material_name}")
            print(f"- Sampler:        {sampler_name}")
        print("-")
        error = True
    else:
        # Check if the filename is in the list of exceptions
        if os.path.basename(listed_file_path) in FILE_NAME_EXCEPTION_LIST:
            return True

        file_path_check = False
        file_path_short = None
        error_file_missing = False

        # Check if the file path is a relative path and the file exists in the path indicated
        if listed_file_path.startswith('./'):

            # Remove the "./" from the path
            file_subpath = listed_file_path[2:]
            file_path = os.path.join(os.path.dirname(xml_path), file_subpath)

            file_path_check = True

        # Check if the file path points to the uniform common folder and the file exists in the Common folder of the export
        elif listed_file_path.startswith('model/character/uniform/common/'):

            # If the PES version is 16 and the file is a model file, throw an error
            if pes_version == 16 and listed_file_type == "Model":
                print(f"- ERROR - {listed_file_type} files cannot be loaded from the Common folder on PES16")
                print(f"- Folder:         {xml_folder_name}")
                print(f"- {xml_extension} name:       {xml_name}")
                print(f"- Model path:     {listed_file_path}")
                print("-")
                return False

            # Remove the "file/character/uniform/common/XXX/" from the path
            file_subpath = listed_file_path[35:]
            common_folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(xml_path))), "Common")
            file_path = os.path.join(common_folder_path, file_subpath)

            file_path_check = True

        # Check if the file path points to the face common folder
        elif listed_file_path.startswith('model/character/face/common/'):
            pass

        # If the file path is not a relative path nor points to the common folders, it is unusable
        else:
            file_path_short = "Unknown"

            error_file_missing = True

        if file_path_check:
            # Replace * in the path with "win32"
            file_path = file_path.replace('*', 'win32')

            error_file_missing = not file_exists(file_path)

        if error_file_missing:

            if not file_path_short:
                # Remove "extracted_exports/" from the path
                file_path_short = file_path[18:]

            ##TODO: Make error-only once the templates have been updated
            if listed_file_type == "Texture":
                print(f"- Warning - {listed_file_type} file does not exist in the path indicated")
            else:
                print(f"- ERROR - {listed_file_type} file does not exist in the path indicated")
            print(f"- Folder:         {xml_folder_name}")
            print(f"- {xml_extension} name:       {xml_name}")
            if listed_file_type == "Texture":
                print(f"- Material:       {material_name}")
                print(f"- Sampler:        {sampler_name}")
            type_string_raw = f"{listed_file_type} path:"
            type_string = type_string_raw + " " * (16 - len(type_string_raw))
            print(f"- {type_string}{listed_file_path}")
            print(f"- Full path:      {file_path_short}")
            print("-")

            if listed_file_type != "Texture":
                error = True

    return not error


def face_diff_xml_check(xml_path):
    """
    Checks the given face_diff.xml file.

    Parameters:
        xml_path (str): The path to the .xml file.

    Returns:
        bool: False if the .xml file is valid, True otherwise.
    """

    # Read the necessary parameters
    pause_on_error = int(os.environ.get('PAUSE_ON_ERROR', '1'))

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
        import xml.parsers.expat
        error_string = xml.parsers.expat.ErrorString(e.code)
        line, column = e.position
        print( "- ERROR - Invalid .xml file")
        print(f"- Folder:         {xml_folder_name}")
        print(f"- xml name:       {xml_name}")
        print(f"- Issue:          \"{error_string}\"")
        print(f"- Location:       At or before line {line}, column {column}")
        print("-")

        if pause_on_error:
            input('Press Enter to continue...')

        os.environ["LOG"] = "1"
        return True

    root = tree.getroot()

    error = False

    # Check that the root tag is 'dif'
    if root.tag != 'dif':
        print( "- ERROR - Invalid root tag on the second line")
        print(f"- Folder:         {xml_folder_name}")
        print(f"- xml name:       {xml_name}")
        print(f"- Root tag:       <{root.tag}>")
        print( "- Must be:        <dif>")
        print("-")

        error = True

    if error and pause_on_error:
        input('Press Enter to continue...')

    if error:
        os.environ["LOG"] = "1"

    return error


def xml_check(xml_path, face_neck_needed=False):
    """
    Checks the given .xml file.

    Parameters:
        xml_path (str): The path to the .xml file.

    Returns:
        bool: False if the .xml file is valid, True otherwise.
    """

    # Read the necessary parameters
    pause_on_error = int(os.environ.get('PAUSE_ON_ERROR', '1'))

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
        import xml.parsers.expat
        error_string = xml.parsers.expat.ErrorString(e.code)
        line, column = e.position
        print( "- ERROR - Invalid .xml file")
        print(f"- Folder:         {xml_folder_name}")
        print(f"- xml name:       {xml_name}")
        print(f"- Issue:          \"{error_string}\"")
        print(f"- Location:       At or before line {line}, column {column}")
        print("-")

        if pause_on_error:
            input('Press Enter to continue...')

        os.environ["LOG"] = "1"
        return True

    root = tree.getroot()

    error = False
    warning = False

    # Check that the root tag is 'config'
    if root.tag != 'config':
        print( "- ERROR - Invalid root tag on the second line")
        print(f"- Folder:         {xml_folder_name}")
        print(f"- xml name:       {xml_name}")
        print(f"- Root tag:       <{root.tag}>")
        print( "- Must be:        <config>")
        print("-")

        error = True

    model_type_list = []
    model_material_path_list = []

    for model in root.findall('model'):

        model_type = model.get('type')
        model_path = model.get('path')
        model_material_path = model.get('material')

        model_type_error = False

        if not model_type:
            print( "- ERROR - Missing model type")
            print(f"- Folder:         {xml_folder_name}")
            print(f"- xml name:       {xml_name}")
            if model_path:
                print(f"- Model path:     {model_path}")
            print("-")

            model_type_error = True

        else:
            model_type_list.append(model_type)

        # Check that the model path corresponds to a file in the folder indicated
        model_path_error = not listed_file_check(xml_path, xml_name, xml_folder_name, model_path, "Model")

        # Check that the mtl path corresponds to a file in the folder indicated, if not checked previously
        if (not model_material_path) or (model_material_path not in model_material_path_list):
            model_material_error = not listed_file_check(xml_path, xml_name, xml_folder_name, model_material_path, "Mtl")

            if model_material_path:
                model_material_path_list.append(model_material_path)

        error = (
            error or
            model_type_error or
            model_path_error or
            model_material_error
        )

    dummy_model = None

    # Check if any of the models has the "face_neck" type
    if face_neck_needed and ("face_neck" not in model_type_list):

        # Create a dummy model element and add it to the root
        dummy_model = dummy_element(xml_folder_path, model_material_path_list[0])
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


    if error and pause_on_error:
        input('Press Enter to continue...')

    if error or warning:
        os.environ["LOG"] = "1"

    return error


def mtl_check(mtl_path):
    """
    Checks the given .mtl file.

    Parameters:
        mtl_path (str): The path to the .mtl file.

    Returns:
        bool: False if the .mtl file is valid, True otherwise.
    """

    # Read the necessary parameters
    pause_on_error = int(os.environ.get('PAUSE_ON_ERROR', '1'))

    # Store the name of the file and its parent folder
    mtl_name = os.path.basename(mtl_path)
    mtl_folder_name = os.path.basename(os.path.dirname(mtl_path))

    # Try to unzlib the file
    unzlib_file(mtl_path)

    # Parse the file
    try:
        tree = ET.parse(mtl_path)
    except ET.ParseError as e:
        import xml.parsers.expat
        error_string = xml.parsers.expat.ErrorString(e.code)
        line, column = e.position
        print( "- ERROR - Invalid .mtl file")
        print(f"- Folder:         {mtl_folder_name}")
        print(f"- MTL name:       {mtl_name}")
        print(f"- Issue:          \"{error_string}\"")
        print(f"- Location:       At or before line {line}, column {column}")
        print("-")

        if pause_on_error:
            input('Press Enter to continue...')

        os.environ["LOG"] = "1"
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
    warning = False

    material_name_list = []

    for material in root.findall('material'):

        error_conflict = False

        # Check if the name of the material is in the list of material names
        if material.get('name') in material_name_list:
            print( "- ERROR - Material listed more than once")
            print(f"- MTL name:       {mtl_name}")
            print(f"- Material:       \"{material.get('name')}\"")
            print("-")

            error_conflict = True

        # Add the name of the material to the list
        material_name = material.get('name')
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
                print("- ERROR - Value of state \"ztest\" must be 1")
                print(f"- MTL name:       {mtl_name}")
                print(f"- Material:       \"{material.get('name')}\"")
                print(f"- State value:    {state_value}")
                print("-")
                error = True

            # Check that the value of blendmode is 0
            if state_name == 'blendmode' and state_value != '0':
                print("- ERROR - Value of state \"blendmode\" must be 0")
                print(f"- MTL name:       {mtl_name}")
                print(f"- Material:       \"{material.get('name')}\"")
                print(f"- State value:    {state_value}")
                print("-")
                error = True

            # Check that the value of alphablend is 0 or 1
            if state_name == 'alphablend' and state_value not in ['0', '1']:
                print("- ERROR - Value of state \"alphablend\" must be 0 or 1")
                print(f"- MTL name:       {mtl_name}")
                print(f"- Material:       \"{material.get('name')}\"")
                print(f"- State value:    {state_value}")
                print("-")
                error = True

        # Make a list of state names missing from the list of required state names
        missing_state_names = [state_name for state_name in REQUIRED_STATE_NAMES if state_name not in state_name_dict]

        if missing_state_names:
            ##TODO: Convert to error once the templates have been updated
            ##print("- ERROR - Missing state names")
            print("- Warning - Missing state names")
            print(f"- Folder:         {mtl_folder_name}")
            print(f"- MTL name:       {mtl_name}")
            print(f"- Material:       \"{material.get('name')}\"")
            # Print the list of missing required state names
            for missing_state_name in missing_state_names:
                print(f"- State name:     \"{missing_state_name}\"")
            print("-")
            ##error = True
            warning = True

        else:
            warning_nonrecvals = False

            # Check that if the value of alphablend is 1, then the value of alphatest is 0
            if state_name_dict['alphablend'] == '1' and not (state_name_dict['zwrite'] == '0'):
                alphablend_recommended_string = 'recommended 1 if semitransparency is needed, 0 otherwise'
                zwrite_recommended_string = 'recommended 0'

                warning_nonrecvals = True

            # Check that if the value of alphablend is 0, then the value of zwrite is 1
            if state_name_dict['alphablend'] == '0' and not (state_name_dict['zwrite'] == '1'):
                alphablend_recommended_string = 'recommended 0 if semitransparency is not needed, 1 otherwise'
                zwrite_recommended_string = 'recommended 1'

                warning_nonrecvals = True

            if warning_nonrecvals:
                print("- Warning - Non-recommended values for states \"alphablend\" and \"zwrite\"")
                print(f"- Folder:         {mtl_folder_name}")
                print(f"- MTL name:       {mtl_name}")
                print(f"- Material:       \"{material.get('name')}\"")
                print(f"- alphablend:     {state_name_dict['alphablend']} ({alphablend_recommended_string})")
                print(f"- zwrite:         {state_name_dict['zwrite']} ({zwrite_recommended_string})")
                print("-")
                warning = True

        # Check, for each sampler, that the texture path corresponds to a texture file in the folder indicated
        for sampler in material.findall('sampler'):

            sampler_name = sampler.get('name')
            sampler_texture_path = sampler.get('path')

            ##TODO: Unify once the templates have been updated
            if not sampler_texture_path:
                print("- ERROR - Missing texture path")
                print(f"- Folder:         {mtl_folder_name}")
                print(f"- MTL name:       {mtl_name}")
                print(f"- Material:       \"{material_name}\"")
                print(f"- Sampler:        \"{sampler_name}\"")
                print("-")
                error = True
            else:

                texture_path_error = not listed_file_check(mtl_path, mtl_name, mtl_folder_name, sampler_texture_path, "Texture", material_name, sampler_name)

                if texture_path_error:
                    ##error = True
                    warning = True


    if error and pause_on_error:
        input('Press Enter to continue...')

    if error or warning:
        os.environ["LOG"] = "1"

    return error
