import xml.etree.ElementTree as ET

from .utils.zlib_plus import unzlib_file
from .utils.id_change import path_id_change


def mtl_id_change(mtl_path, team_id = "000"):
    """
    Change the team ID in the given .mtl file.

    Parameters:
        mtl_path (str): The path to the .mtl file.
        team_id (str, optional): The team ID to replace in the file. Defaults to "000".

    This function looks for model/character/uniform/common/XXX/, u0XXXp and u0XXXg inside the path of the samplers,
    where XXX is any sequence of three characters, and replaces XXX with the team ID provided as parameter.
    """

    # Try to unzlib the file
    unzlib_file(mtl_path)

    # Parse the file
    try:
        tree = ET.parse(mtl_path)
    except ET.ParseError:
        print(f"- ERROR: {mtl_path} is not a valid .mtl file")
        input('Press Enter to continue...')
        return True

    root = tree.getroot()

    modified = False

    for sampler in root.findall('.//sampler'):
        path = sampler.get('path')
        if path is not None:
            new_path = path_id_change(path, team_id)

            if new_path != path:
                modified = True
                path = new_path

            sampler.set('path', path)

    if modified:
        tree.write(mtl_path, "UTF-8")
