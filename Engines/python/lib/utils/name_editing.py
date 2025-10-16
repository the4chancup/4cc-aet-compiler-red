import os
import re

from .zlib_plus import unzlib_file
from .FILE_INFO import UNIFORM_COMMON_PREFOX_PATH


def normalize_kit_dependent_file(file_name):
    """
    Check if a file is kit-dependent (u0XXXp1-9) and return the normalized p0 version.

    Parameters:
        file_name (str): The filename to check

    Returns:
        str: The normalized filename with p0, or the original filename if not kit-dependent
    """
    # Match u0XXXp[1-9] where XXX is any three alphanumeric characters
    match = re.search(r'u0([a-zA-Z0-9]{3})p[1-9]', file_name)
    if match:
        # Replace the kit number with 0
        return re.sub(r'(u0[a-zA-Z0-9]{3}p)[1-9]', r'\g<1>0', file_name)
    return file_name


def is_common_file(file_name):
    """
    Check if a file should be loaded from the Common folder and return the cleaned filename.

    Parameters:
        file_name (str): The filename, possibly with .common or .common.txt extension

    Returns:
        str or None: The cleaned filename (without .common/.common.txt) if it's a common file
            marker, None otherwise
    """
    # If the file is a marker file, return the cleaned name
    if file_name.endswith('.common.txt'):
        return file_name[:-11]
    elif file_name.endswith('.common'):
        return file_name[:-7]

    return None


def model_names_fix(folder_path, include_subfolders=True):
    '''Add "oral_" and "_win32" to any model names found in the folder and its subfolders'''

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        if not os.path.isfile(file_path) or not file_name.endswith(".model"):
            continue

        # Check if the file name starts with "oral_" and ends with "_win32"
        file_name_noext = os.path.splitext(file_name)[0]
        if file_name_noext.startswith("oral_") and file_name_noext.endswith("_win32"):
            continue

        file_path_new = os.path.join(folder_path, f"oral_{file_name_noext}_win32.model")
        if os.path.exists(file_path_new):
            os.remove(file_path_new)
        os.rename(file_path, file_path_new)

    if not include_subfolders:
        return

    for subfolder_name in os.listdir(folder_path):
        subfolder_path = os.path.join(folder_path, subfolder_name)
        if os.path.isdir(subfolder_path):
            model_names_fix(subfolder_path, include_subfolders)


def filenames_id_replace(folder_path, team_id, include_subfolders=True):
    '''Replace the dummy team ID with the actual one in any filenames found in the folder and its subfolders'''

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        if not os.path.isfile(file_path):
            continue

        # Look for u0XXXp and u0XXXg and replace them with the actual team ID
        file_path_new = path_id_change(file_path, team_id, common_replace=False)

        if file_path_new == file_path:
            continue

        if os.path.exists(file_path_new):
            os.remove(file_path_new)
        os.rename(file_path, file_path_new)

    if not include_subfolders:
        return

    for subfolder_name in os.listdir(folder_path):
        subfolder_path = os.path.join(folder_path, subfolder_name)
        if os.path.isdir(subfolder_path):
            filenames_id_replace(subfolder_path, team_id, include_subfolders)


def fix_mtl_paths(file_path, team_id):
    '''Replace any relative paths with absolute ones to the team's common folder'''

    with open(file_path, 'r') as file:
        lines = file.readlines()
    with open(file_path, 'w') as file:
        for line in lines:
            if line.startswith("./"):
                file.write(f"{UNIFORM_COMMON_PREFOX_PATH}{team_id}/")
            file.write(line)


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


def txt_id_change(file_path, team_id):
    """
    Change the team ID in the given text file.

    Parameters:
        file_path (str): The path to the file.
        team_id (str): The team ID to replace in the file.

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
