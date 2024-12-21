import re

from .zlib_plus import unzlib_file


def path_id_change(path, team_id, common_replace=True):
    """
    Change the team ID in the given path string.

    Parameters:
        path (str): The path string.
        team_id (str): The team ID to replace in the file.

    This function looks for common/XXX/, u0XXXp and u0XXXg inside the path string,
    where XXX is any sequence of three characters, and replaces XXX with the team ID provided as parameter.
    """
    if common_replace:
        path = re.sub(r"common/([a-zA-Z0-9]{3})/", f"common/{team_id}/", path)
    path = re.sub(r"u0([a-zA-Z0-9]{3})p", f"u0{team_id}p", path)
    path = re.sub(r"u0([a-zA-Z0-9]{3})g", f"u0{team_id}g", path)

    return path


def txt_id_change(file_path, team_id = "000"):
    """
    Change the team ID in the given text file.

    Parameters:
        file_path (str): The path to the file.
        team_id (str, optional): The team ID to replace in the file. Defaults to "000".

    This function looks for common/XXX/, u0XXXp and u0XXXg inside each line,
    where XXX is any sequence of three characters, and replaces XXX with the team ID provided as parameter.
    """

    # Try to unzlib the file
    unzlib_file(file_path)

    # Read the file line by line
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    modified = False

    # Replace the team ID in the file
    for i, line in enumerate(lines):
        new_line = path_id_change(line, team_id)

        if new_line == line:
            continue

        modified = True
        lines[i] = new_line

    if not modified:
        return

    with open(file_path, 'w', encoding="utf8") as file:
        file.writelines(lines)

    return
