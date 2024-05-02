import os
import py7zr
import shutil
import requests
import webbrowser
from datetime import datetime
from datetime import timedelta


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


def version_last_find(owner, repo):
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


def version_last_download(owner, repo, ver, ext, folder):
    """
    Get the latest version of a GitHub repository based on the owner and repo name.

    Parameters:
    - owner (str): The owner of the repository.
    - repo (str): The name of the repository.
    - ver (str): The version of the repository to download.
    - ext (str): The extension of the file to download.
    - folder (str): The folder to download the repository to.

    Returns:
    - str: The filename of the downloaded file, or None if the download failed.
    """

    file_name = f"{repo}.{ver}.{ext}"

    url = f"https://github.com/{owner}/{repo}/releases/download/{ver}/{file_name}"

    try:
        response = requests.get(url)

    except requests.exceptions.ConnectionError:
        print("- Failed to connect to GitHub API, cannot download latest version")
        return None

    if response.status_code == 200:
        with open(f"{folder}/{file_name}", "wb") as f:
            f.write(response.content)

        return file_name

    return None


def update_get(app_owner, app_name, version_last, update_major=False):
    """
    Download the latest version of the application to the parent folder of the program folder.

    Parameters:
    - app_owner: The owner of the application.
    - app_name: The name of the application.
    - version_last: The last version of the application.
    - update_major: A boolean flag indicating whether it's a major update (default is False).

    Returns:
    - None
    """

    # Download the latest version to the parent folder of the program folder
    app_folder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app_folder_parent = os.path.dirname(app_folder)

    print("-")
    print("- Updating...")

    file_name = version_last_download(app_owner, app_name, version_last, "7z", app_folder_parent)

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

    app_name_new = app_name + " " + version_last
    app_new_folder = os.path.join(app_folder_parent, app_name_new)

    if not update_major:
        # Copy the settings ini to the new folder after deleting the one in the old folder
        if os.path.exists(os.path.join(app_new_folder, "settings.ini")):
            os.remove(os.path.join(app_new_folder, "settings.ini"))
        shutil.copy(os.path.join(app_folder, "settings.ini"), app_new_folder)

    # Move the contents of the exports_to_add folder to the new folder after deleting the one in the old folder
    for file in os.listdir(os.path.join(app_folder, "exports_to_add")):
        shutil.move(os.path.join(app_folder, "exports_to_add", file), os.path.join(app_new_folder, "exports_to_add"))

    print("-")
    print("- Successfully downloaded and unpacked the latest version")
    print("- The exports in the \"exports_to_add\" folder have been moved over")
    if not update_major:
        print("- The settings file has also been copied to the new folder")
    else:
        print("- The settings file has been overhauled, so you will need to edit it manually")
    print("-")
    print("- The old folder has been preserved, so you can delete it later")
    print("-")
    if not update_major:
        input("Press Enter to open the new folder...")

        # Open the unpacked folder in the default file explorer
        os.startfile(app_new_folder)
    else:
        input("Press Enter to open the new folder, and the old and new settings files...")

        # Open the old settings file and the new settings file
        os.startfile(os.path.join(app_folder, "settings.ini"))
        os.startfile(os.path.join(app_new_folder, "settings.ini"))

        # Open the unpacked folder in the default file explorer
        os.startfile(app_new_folder)


def updates_disable():
    """Disables update checking"""

    with open("./settings.ini", "r") as f:
        lines = f.readlines()

    with open("./settings.ini", "w") as f:
        for line in lines:
            if line.startswith("updates_check"):
                line = "updates_check = 0\n"

            f.write(line)

    print("-")
    print("- Updates Checking has been disabled")


def update_check(app_owner, app_name, major, minor, patch, minutes_between_checks=120):
    """
    Check for updates on github based on the input major, minor, and patch numbers.
    Returns the type of update available: Major, Minor, Bugfix, or None.
    """

    releases_url = f"https://github.com/{app_owner}/{app_name}/releases/"

    CHECK_LAST_FILE = "./Engines/update_last_check.txt"
    SKIP_LAST_FILE = "./Engines/update_last_skip.txt"

    # Check the current time
    now = datetime.now()

    # Read the last check time
    if os.path.exists(CHECK_LAST_FILE):
        with open(CHECK_LAST_FILE, "r") as f:
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

    version_last = version_last_find(app_owner, app_name)

    # If the version could not be checked, return None
    if version_last is None:
        return None

    version_last_list = version_last.split(".")

    update_major = False
    if int(version_last_list[0]) > major:
        update_available = "Major"
        update_major = True
    elif int(version_last_list[1]) > minor:
        update_available = "Minor"
    elif int(version_last_list[2]) > patch:
        update_available = "Bugfix"
    else:
        update_available = None

    if update_available is None:
        print("-")
        print("- You are running the latest version")

        return None

    print(f"- The latest version is {version_last}")

    # Save the current time
    with open(CHECK_LAST_FILE, "w") as f:
        f.write(now.strftime("%Y-%m-%d %H:%M:%S"))

    # Read the last skipped version
    if os.path.exists(SKIP_LAST_FILE):
        with open(SKIP_LAST_FILE, "r") as f:
            skip_last = f.read()
    else:
        skip_last = None

    # Check if the latest version is the same as the last skipped version
    if skip_last is not None:
        if version_last == skip_last:
            print("- (This version has been skipped)")
            return None

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
        question = input("Or just press Enter to continue normally...")

        if question == "info":
            # Open the website in the default browser
            webbrowser.open(releases_url)
        else:
            break

    match question:
        case "up":
            # Update the program
            update_get(app_owner, app_name, version_last, update_major)

            exit()

        case "skip":
            # Save the latest version
            with open(SKIP_LAST_FILE, "w") as f:
                f.write(version_last)

        case "fuckoff":
            # Set updates_check on the settings ini to 0
            updates_disable()

            return None

        case _:
            pass

    return update_available
