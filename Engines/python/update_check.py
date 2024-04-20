import os
import requests
import webbrowser
from datetime import datetime
from datetime import timedelta


def website_exist(url, major, minor, patch):
    """
    Check if a specific version of the website exists based on the major, minor, and patch numbers.
    Makes a HEAD request to the website, and checks if the response status code is less than 400.

    Parameters:
    - major (int): The major version number.
    - minor (int): The minor version number.
    - patch (int): The patch version number.

    Returns:
    - bool: True if the website version exists, False otherwise.
    """

    version_string = str(major) + '.' + str(minor) + '.' + str(patch)
    version_url = url + version_string

    response = requests.head(version_url)
    exist = (response.status_code < 400)

    return exist


def update_check(app_name, major, minor, patch, minutes_between_checks=120):
    """
    Check for updates on github based on the input major, minor, and patch numbers.
    Returns the type of update available: Major, Minor, Bugfix, or None.
    """

    releases_url = f"https://github.com/the4chancup/{app_name}/releases/"
    tags_url = f"{releases_url}tag/"

    last_check_file = "./Engines/update_last_check.txt"

    # Check the current time
    now = datetime.now()

    # Read the last check time
    if os.path.exists(last_check_file):
        with open(last_check_file, "r") as f:
            last_check = f.read()
    else:
        last_check = None

    # Save the current time
    with open(last_check_file, "w") as f:
        f.write(now.strftime("%Y-%m-%d %H:%M:%S"))

    # Check if it's time to check for updates
    if last_check is not None:
        last_check = datetime.strptime(last_check, "%Y-%m-%d %H:%M:%S")
        if now - last_check < timedelta(minutes=minutes_between_checks):
            return None

    print("-")
    print("- Checking for updates...")

    if website_exist(tags_url, major+1, minor, patch):
        update_available = "Major"
    elif website_exist(tags_url, major, minor+1, patch):
        update_available = "Minor"
    elif website_exist(tags_url, major, minor, patch+1):
        update_available = "Bugfix"
    else:
        update_available = None

    if update_available is None:
        print("-")
        print("- You are running the latest version")
    else:
        print("-")
        print(f"- <{update_available} update available>")
        print("-")
        print("- Please download it from the github Releases page")
        print("- You can still use this version, but updating is recommended")
        print("- to stay up-to-date with the latest features and bugfixes")

        print("-")
        question = input("Type \"up\" and press Enter to open the page, or just press Enter to continue...")
        if question == "up":
            # Open the website in the default browser
            webbrowser.open(releases_url)
            exit()

    return update_available
