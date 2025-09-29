import urllib.error
import urllib.request


def version_download(owner, repo, ver, ext, folder):
    """
    Get the version of a GitHub repository based on the owner and repo name.

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
        response = urllib.request.urlopen(url)
        if response.status == 200:
            with open(f"{folder}/{file_name}", "wb") as f:
                f.write(response.read())
            response.close()
            return file_name
        else:
            response.close()
            return None
    except (urllib.error.URLError, urllib.error.HTTPError):
        print("- Failed to connect to GitHub API, cannot download package")
        return None
