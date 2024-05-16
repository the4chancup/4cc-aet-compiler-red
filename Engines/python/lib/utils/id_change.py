import re


def path_id_change(path, team_id):
    """
    Change the team ID in the given path string.

    Parameters:
        path (str): The path string.
        team_id (str): The team ID to replace in the file.

    This function looks for model/character/uniform/common/XXX/, u0XXXp and u0XXXg inside the path string,
    where XXX is any sequence of three characters, and replaces XXX with the team ID provided as parameter.
    """

    path = re.sub(r'model/character/uniform/common/([a-zA-Z0-9]){3}/', 'model/character/uniform/common/'+team_id+'/', path)
    path = re.sub(r'u0([a-zA-Z0-9]){3}p', 'u0'+team_id+'p', path)
    path = re.sub(r'u0([a-zA-Z0-9]){3}g', 'u0'+team_id+'g', path)

    return path
