import xml.etree.ElementTree as ET
import re

def mtl_id_change(mtl_path, team_id = "000"):
    """
    Change the team ID in the given .mtl file.

    Parameters:
        mtl_path (str): The path to the .mtl file.
        team_id (str, optional): The team ID to replace in the file. Defaults to "000".

    This function looks for /XXX/ or for u0XXXp inside the path of the samplers,
    where XXX is any sequence of three digits, and replaces XXX with the team ID provided as parameter.
    """

    tree = ET.parse(mtl_path)
    root = tree.getroot()

    for sampler in root.findall('.//sampler'):
        path = sampler.get('path')
        if path is not None:
            path = re.sub(r'/(\d){3}/', '/'+team_id+'/', path)
            path = re.sub(r'u0(\d){3}p', 'u0'+team_id+'p', path)
            sampler.set('path', path)

    tree.write(mtl_path)
