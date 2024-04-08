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

    # Store the name of the parent folder
    mtl_folder_name = os.path.basename(os.path.dirname(mtl_path))
    
    # Store the name of the mtl and its parent folder
    mtl_name = os.path.join(mtl_folder_name, os.path.basename(mtl_path))
    
    # Try to unzlib the file
    unzlib_file(mtl_path)
    
    # Parse the file
    try:
        tree = ET.parse(mtl_path)
    except:
        print(f"- ERROR: {mtl_name} is not a valid .mtl file")
        input('Press Enter to continue...')
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
    
    for material in root.findall('material'):
        
        # Create dictionary of state names and values
        state_name_dict = {}
        for state in material.findall('state'):
            name = state.get('name')
            value = state.get('value')
            state_name_dict[name] = value
        
            # Check that the value of ztest is 1
            if name == 'ztest' and value != '1':
                print(f"- ERROR: ztest must be 1 in the material \"{material.get('name')}\"")
                print(f"- in {mtl_name}")
                print("-")
                error = True
            
            # Check that the value of blendmode is 0
            if name == 'blendmode' and value != '0':
                print(f"- ERROR: blendmode must be 0 in the material \"{material.get('name')}\"")
                print(f"- in {mtl_name}")
                print("-")
                error = True
            
            # Check that the value of alphablend is 0 or 1
            if name == 'alphablend' and value not in ['0', '1']:
                print(f"- ERROR: alphablend must be 0 or 1 in the material \"{material.get('name')}\"")
                print(f"- in {mtl_name}")
                print("-")
                error = True
            
        # Make a list of state names missing from the list of required state names
        missing_state_names = [state_name for state_name in REQUIRED_STATE_NAMES if state_name not in state_name_dict]
        
        if missing_state_names:
            ##TODO: Remove once the templates have been updated
            continue
            print("- ERROR: The following required state names are missing")
            print(f"- from the material \"{material.get('name')}\" in {mtl_name}:")
            # Print the list of missing required state names
            print("- " + "\n- ".join(missing_state_names))
            print("-")
            error = True
        
        else:
            # Check that if the value of alphablend is 1, then the value of alphatest is 0
            if state_name_dict['alphablend'] == '1' and not (state_name_dict['zwrite'] == '0'):
                print(f"- Warning: Non-recommended values for the material \"{material.get('name')}\"")
                print(f"- in {mtl_name}:")
                print(f"- alphablend: {state_name_dict['alphablend']} (recommended 1 if semitransparency is needed, 0 otherwise)")
                print(f"- zwrite:     {state_name_dict['zwrite']} (recommended 0)")
                print("-")
                
            # Check that if the value of alphablend is 0, then the value of zwrite is 1
            if state_name_dict['alphablend'] == '0' and not (state_name_dict['zwrite'] == '1'):
                print(f"- Warning: Non-recommended values for the material \"{material.get('name')}\"")
                print(f"- in {mtl_name}:")
                print(f"- alphablend: {state_name_dict['alphablend']} (recommended 0 if semitransparency is not needed, 1 otherwise)")
                print(f"- zwrite:     {state_name_dict['zwrite']} (recommended 1)")
                print("-")
    
    if error:
        input('Press Enter to continue...')

    return error
