import os
import xml.etree.ElementTree as ET

from .utils.zlib_plus import unzlib_file

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
        print("- ERROR - Invalid .mtl file")
        print(f"- Folder:      {mtl_folder_name}")
        print(f"- MTL name:    {mtl_name}")
        print(f"- Issue:       \"{error_string}\"")
        print(f"- Location:    At or before line {line}, column {column}")
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
    
    previous_material_name_list = []
    
    for material in root.findall('material'):
        
        error_conflict = False
        
        # Check if the name of the material is in the list of previous material names
        if material.get('name') in previous_material_name_list:
            print(f"- ERROR - The material \"{material.get('name')}\" in {mtl_name}")
            print("- is listed more than once")
            print("-")
            
            error_conflict = True
        
        # Add the name of the material to the list
        previous_material_name_list.append(material.get('name'))
        
        if error_conflict:
            error = True
            continue

        # Create dictionary of state names and values
        state_name_dict = {}
        for state in material.findall('state'):
            name = state.get('name')
            value = state.get('value')
            state_name_dict[name] = value
        
            # Check that the value of ztest is 1
            if name == 'ztest' and value != '1':
                print("- ERROR - Value of state \"ztest\" must be 1")
                print(f"- MTL name:    {mtl_name}")
                print(f"- Material:    \"{material.get('name')}\"")
                print(f"- State value: {value}")
                print("-")
                error = True
            
            # Check that the value of blendmode is 0
            if name == 'blendmode' and value != '0':
                print("- ERROR - Value of state \"blendmode\" must be 0")
                print(f"- MTL name:    {mtl_name}")
                print(f"- Material:    \"{material.get('name')}\"")
                print(f"- State value: {value}")
                print("-")
                error = True
            
            # Check that the value of alphablend is 0 or 1
            if name == 'alphablend' and value not in ['0', '1']:
                print("- ERROR - Value of state \"alphablend\" must be 0 or 1")
                print(f"- MTL name:    {mtl_name}")
                print(f"- Material:    \"{material.get('name')}\"")
                print(f"- State value: {value}")
                print("-")
                error = True
            
        # Make a list of state names missing from the list of required state names
        missing_state_names = [state_name for state_name in REQUIRED_STATE_NAMES if state_name not in state_name_dict]
        
        if missing_state_names:
            ##TODO: Convert to error once the templates have been updated
            ##print("- ERROR - Missing state names")
            print("- Warning - Missing state names")
            print(f"- Folder:      {mtl_folder_name}")
            print(f"- MTL name:    {mtl_name}")
            print(f"- Material:    \"{material.get('name')}\"")
            # Print the list of missing required state names
            for missing_state_name in missing_state_names:
                print(f"- State name:  \"{missing_state_name}\"")
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
                print(f"- Folder:      {mtl_folder_name}")
                print(f"- MTL name:    {mtl_name}")
                print(f"- Material:    \"{material.get('name')}\"")
                print(f"- alphablend:  {state_name_dict['alphablend']} ({alphablend_recommended_string})")
                print(f"- zwrite:      {state_name_dict['zwrite']} ({zwrite_recommended_string})")
                print("-")
                warning = True
        
        # Check, for each sampler, that the texture path corresponds to a texture file in the folder indicated
        for sampler in material.findall('sampler'):
            sampler_texture_path = sampler.get('path')
            
            if not sampler_texture_path:
                print("- ERROR - Missing texture path")
                print(f"- Folder:      {mtl_folder_name}")
                print(f"- MTL name:    {mtl_name}")
                print(f"- Material:    \"{material.get('name')}\"")
                print(f"- Sampler:     \"{sampler.get('name')}\"")
                print("-")
                error = True
            else:
                error_texture_missing = False
                
                # Check if the texture path is a relative path and the file exists in the path indicated
                if sampler_texture_path.startswith('./'):
                    # Remove the "./" from the path
                    texture_subpath = sampler_texture_path[2:]
                    texture_path = os.path.join(os.path.dirname(mtl_path), texture_subpath)
                    
                    if not os.path.exists(texture_path):
                        # Remove "extracted_exports/" from the path
                        texture_path_short = texture_path[18:]
                        
                        error_texture_missing = True
                
                # Check if the texture path points to the uniform common folder and the file exists in the Common folder of the export
                elif sampler_texture_path.startswith('model/character/uniform/common/'):
                    # Remove the "model/character/uniform/common/XXX/" from the path
                    texture_subpath = sampler_texture_path[35:]
                    common_folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(mtl_path))), "Common")
                    texture_path = os.path.join(common_folder_path, texture_subpath)
                    
                    if not os.path.exists(texture_path):
                        # Remove "extracted_exports/" from the path
                        texture_path_short = texture_path[18:]
                        
                        error_texture_missing = True
                
                # Check if the texture path points to the face common folder
                elif sampler_texture_path.startswith('model/character/face/common/'):
                    pass
                
                # If the texture path is not a relative path nor points to the common folders, it is unusable
                else:
                    texture_path_short = "Unknown"
                    
                    error_texture_missing = True
                    
                if error_texture_missing:
                    ##TODO: Convert to error once the templates have been updated
                    ##print("- ERROR - Texture file does not exist in the path indicated")
                    print("- Warning - Texture file does not exist in the path indicated")
                    print(f"- Folder:      {mtl_folder_name}")
                    print(f"- MTL name:    {mtl_name}")
                    print(f"- Material:    \"{material.get('name')}\"")
                    print(f"- Sampler:     \"{sampler.get('name')}\"")
                    print(f"- Tex path:    {sampler_texture_path}")
                    print(f"- Full path:   {texture_path_short}")
                    print("-")
                    ##error = True
                    warning = True
                
    
    if error and pause_on_error:
        input('Press Enter to continue...')
    
    if error or warning:
        os.environ["LOG"] = "1"

    return error
