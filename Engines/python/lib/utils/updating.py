import os
import py7zr
import shutil
import filecmp
import difflib
import requests
import webbrowser
from datetime import datetime
from datetime import timedelta

from .pausing import pause
from .version_downloading import version_download
from .settings_management import settings_transfer
from .FILE_INFO import (
    TEAMS_LIST_PATH,
    EXPORTS_TO_ADD_PATH,
    SETTINGS_PATH,
    SETTINGS_TRANSFER_TABLE_PATH,
    CHECK_LAST_PATH,
    SKIP_LAST_PATH,
)


def website_exist(url):
    """
    Check if a website exists based on the URL.
    Makes a HEAD request to the website, and checks if the response status code is less than 400.

    Parameters:
    - url (str): The URL of the website.

    Returns:
    - bool: True if the website version exists, False otherwise.
    """

    try:
        response = requests.head(url)
        exist = (response.status_code < 400)
    except requests.exceptions.ConnectionError:
        print("- Failed to connect to website, cannot check if it exists")
        exist = False

    return exist


def version_latest_find(owner, repo):
    """
    Find the latest version of a GitHub repository based on the owner and repo name.
    Returns the latest version as a string.

    Parameters:
    - owner (str): The owner of the repository.
    - repo (str): The name of the repository.

    Returns:
    - str: The latest version as a string.
    - str: The description of the latest version.
    """

    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    version = None

    try:
        response = requests.get(url)

    except requests.exceptions.ConnectionError:
        print("- Failed to connect to GitHub API, cannot check for updates")
        return None

    if response.status_code == 200:
        data = response.json()
        version = data["tag_name"]

    return version


def update_get(app_owner, app_name, version_latest, update_major=False):
    """
    Download the latest version of the application to the parent folder of the program folder.

    Parameters:
    - app_owner: The owner of the application.
    - app_name: The name of the application.
    - version_latest: The latest version of the application.
    - update_major: A boolean flag indicating whether it's a major update (default is False).

    Returns:
    - None
    """

    # Download the latest version to the parent folder of the working folder
    app_folder = os.getcwd()
    app_folder_parent = os.path.dirname(app_folder)

    print("-")
    print("- Updating...")

    file_name = version_download(app_owner, app_name, version_latest, "7z", app_folder_parent)

    if file_name is None:
        print("-")
        print("- Failed to download the latest version")

        return

    file_path = os.path.join(app_folder_parent, file_name)

    # Unpack the 7z file to the parent folder using py7zr
    with py7zr.SevenZipFile(file_path, mode="r") as archive:
        archive.extractall(app_folder_parent)

    # Delete the 7z file
    os.remove(file_path)

    app_name_new = app_name + " " + version_latest
    app_new_folder = os.path.join(app_folder_parent, app_name_new)

    settings_new_path = os.path.join(app_new_folder, os.path.basename(SETTINGS_PATH))

    if not update_major:
        # Copy the settings ini to the new folder after deleting the one in the old folder
        if os.path.exists(settings_new_path):
            os.remove(settings_new_path)
        shutil.copy(SETTINGS_PATH, app_new_folder)

    else:
        # Check if the new version has a transfer table
        transfer_table_path = None
        if os.path.exists(SETTINGS_TRANSFER_TABLE_PATH):
            transfer_table_path = SETTINGS_TRANSFER_TABLE_PATH

        # Transfer the settings from the old ini to the new one
        settings_added, settings_removed, settings_renamed = (
            settings_transfer(SETTINGS_PATH, settings_new_path, transfer_table_path)
        )

    # Check if the teams_list.txt file is different from the new one
    if not update_major:

        TEAMS_LIST_NAME = os.path.basename(TEAMS_LIST_PATH)
        teams_list_new_path = os.path.join(app_new_folder, TEAMS_LIST_NAME)

        if not filecmp.cmp(TEAMS_LIST_PATH, teams_list_new_path):

            print( "-")
            print(f"- A new different \"{TEAMS_LIST_NAME}\" file is available in the new version")
            print( "-")
            pause("Press any key to see the differences... ")
            # Print the differences between the two files
            with open(teams_list_new_path, "r", encoding='utf-8') as f1:
                with open(TEAMS_LIST_PATH, "r", encoding='utf-8') as f2:
                    diff = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile=TEAMS_LIST_NAME + " current", tofile=TEAMS_LIST_NAME + " new")
                    for line in diff:
                        print(line, end="")
            print("-")
            response = input("Type \"new\" to use the new file, or just press Enter to keep the current one... ")

            if "new" not in response:
                if os.path.exists(teams_list_new_path):
                    os.remove(teams_list_new_path)
                shutil.copy(TEAMS_LIST_PATH, app_new_folder)

    # Move the contents of the exports_to_add folder to the new folder after deleting the one in the old folder
    EXPORTS_TO_ADD_NAME = os.path.basename(EXPORTS_TO_ADD_PATH)
    for file in os.listdir(EXPORTS_TO_ADD_PATH):
        shutil.move(os.path.join(EXPORTS_TO_ADD_PATH, file), os.path.join(app_new_folder, EXPORTS_TO_ADD_PATH))

    print( "-")
    print( "- Successfully downloaded and unpacked the latest version")
    print(f"- The exports in the \"{EXPORTS_TO_ADD_NAME}\" folder have been moved over")
    print( "-")
    if not update_major:
        print("- The settings file has also been copied to the new folder")
    else:
        print("- The settings file has been overhauled, but the settings")
        print("- from the current settings file have been transferred to it")
        if settings_renamed:
            print("-")
            print("- The following settings have been renamed, and their values transferred:")
            for setting in settings_renamed:
                print(f"- [{setting[0]}] -> [{setting[1]}]")
        if settings_removed:
            print("-")
            print("- The following settings have been removed:")
            for setting in settings_removed:
                print(f"- [{setting}]")
        if settings_added:
            print("-")
            print("- The following settings have been added:")
            for setting in settings_added:
                print(f"- [{setting}]")
    print("-")
    print("- The old folder has been preserved, so you can delete it later")

    print("-")
    pause("Press any key to open the new folder... ")

    # Open the unpacked folder in the default file explorer
    os.startfile(app_new_folder)


def updates_disable():
    """Disables update checking"""

    with open(SETTINGS_PATH, "r", encoding='utf-8') as f:
        lines = f.readlines()

    with open(SETTINGS_PATH, "w", encoding='utf-8') as f:
        for line in lines:
            if line.startswith("updates_check"):
                line = "updates_check = 0\n"

            f.write(line)

    print("-")
    print("- Updates Checking has been disabled")


def update_check(app_owner, app_name, major, minor, patch, minutes_between_checks=120, check_force=False):
    """
    Check for updates on GitHub for the specified application and provide user with options.

    Parameters:
    - app_owner (str): The owner of the GitHub repository.
    - app_name (str): The name of the GitHub repository.
    - major (int): The major version number.
    - minor (int): The minor version number.
    - patch (int): The patch version number.
    - minutes_between_checks (int): The minimum interval in minutes to wait between checks. Default is 120 minutes.
    - check_force (bool): If True, forces an update check regardless of the last check time.

    Returns:
    - bool: A boolean indicating whether the function completed without initiating an update; True means no update was initiated, False means the current version is up-to-date.
    - None: The function returns None if it's not time to check for updates (based on the interval), or if the latest version could not be checked.
    - Exits: The program will exit if the user chooses to update ('up').

    The function first determines if it's time to perform an update check. It then fetches the latest version from GitHub. If an update is available, it prompts the user with options:
    - 'up' to update the compiler automatically.
    - 'info' to open the GitHub releases page for manual review or update.
    - 'skip' to skip the current version and not be warned until a new version is available.
    - 'fuckoff' to disable future update checking.
    If the user inputs anything else, it continues without updating.
    """

    releases_url = f"https://github.com/{app_owner}/{app_name}/releases/"

    # Check the current time
    now = datetime.now()

    # Read the last check time
    if os.path.exists(CHECK_LAST_PATH) and not check_force:
        with open(CHECK_LAST_PATH, "r", encoding='utf-8') as f:
            check_last = f.read()
    else:
        check_last = None

    # Check if it's time to check for updates
    if check_last is not None:
        check_last = datetime.strptime(check_last, "%Y-%m-%d %H:%M:%S")
        if now - check_last < timedelta(minutes=minutes_between_checks):
            return None

    print("-")
    print("- Checking for updates...")

    version_latest = version_latest_find(app_owner, app_name)

    # If the version could not be checked, return None
    if version_latest is None:
        return None

    # Save the current time
    with open(CHECK_LAST_PATH, "w", encoding='utf-8') as f:
        f.write(now.strftime("%Y-%m-%d %H:%M:%S"))

    version_latest_list = version_latest.split(".")

    update_major = False
    if int(version_latest_list[0]) > major:
        update_available = "Major"
        update_major = True
    elif int(version_latest_list[1]) > minor:
        update_available = "Minor"
    elif int(version_latest_list[2]) > patch:
        update_available = "Bugfix"
    else:
        update_available = None

    if update_available is None:
        print("-")
        print("- You are running the latest version")

        return False

    print(f"- The latest version is {version_latest}")

    # Read the last skipped version
    if os.path.exists(SKIP_LAST_PATH) and not check_force:
        with open(SKIP_LAST_PATH, "r", encoding='utf-8') as f:
            skip_last = f.read()
    else:
        skip_last = None

    # Check if the latest version is the same as the last skipped version
    if skip_last is not None:
        if version_latest == skip_last:
            print("- (This version has been skipped)")
            return True

    print("-")
    print(f"- <{update_available} update available>")
    print("-")
    print("- You can still use the current version, but updating is recommended")
    print("- so you can stay up-to-date with the latest features and bugfixes")

    while True:
        print("-")
        print("- Type one of the following and press Enter...")
        print("  up                        Downloads the new pack and updates the compiler automatically")
        print("  info                      Opens the github releases page so you can check the changelog and choose")
        print("                            whether to update, or even grab the pack and update manually")
        print("  skip                      Skips this version and doesn't warn again until a newer one comes out")
        print("  fuckoff                   Disables update checking (not recommended)")
        print("-")
        response = input("Or just press Enter to continue normally... ")

        if response == "info":
            # Open the website in the default browser
            webbrowser.open(releases_url)
        else:
            break

    match response:
        case "up":
            # Update the program
            update_get(app_owner, app_name, version_latest, update_major)

            exit()

        case "skip":
            # Save the latest version
            with open(SKIP_LAST_PATH, "w", encoding='utf-8') as f:
                f.write(version_latest)

        case "fuckoff":
            # Set updates_check on the settings ini to 0
            updates_disable()

        case _:
            pass

    return True
