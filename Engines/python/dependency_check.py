import sys
import runpy
import subprocess
import importlib.util

from python.lib.utils import COLORS


def dependency_check_on_import():
    """Checks if the dependencies are installed, and if not, installs them."""

    if sys.platform != "win32":
        # Check if imagemagick is installed
        if not subprocess.check_output(["whereis", "convert"]) != b'convert:\n':
            print("-")
            print("- ImageMagick was not found.")
            print("- It is required to convert DDS DX10 textures.")
            print("-")
            print("- Please install ImageMagick and rerun the program.")
            print("-")
            exit()

    # Prepare a list of dependencies as dictionaries with name and name_pip
    dependencies = [
        {
            "name_package": "py7zr",
            "name_pip":     "py7zr",
            "name_user":    "Py7zr (7z extractor)",
        },
        {
            "name_package": "requests",
            "name_pip":     "requests",
            "name_user":    "Requests (HTTP library)",
        },
        {
            "name_package": "commentedconfigparser",
            "name_pip":     "commented-configparser",
            "name_user":    "Commented Config Parser (config file parser)",
        },
        {
            "name_package": "rich",
            "name_pip":     "rich",
            "name_user":    "Rich (rich text console output)",
        },
    ]

    dependencies_missing = []

    for dependency in dependencies:
        if importlib.util.find_spec(dependency["name_package"]) is None:
            # Add any missing dependencies to the list
            dependencies_missing.append(dependency)

    if dependencies_missing:

        print("-")
        print("- The following dependencies were not found:")
        # List the missing dependencies, one per line
        for dependency in dependencies_missing:
            print(f"- \"{dependency['name_user']}\"")

        print("-")
        print("- They will be installed now (or you can close the program now and install them manually).")
        print(f"- {COLORS.DARK_YELLOW}Once the installation is complete, the program will be closed automatically.{COLORS.RESET}")
        print("- Please run it again afterwards.")
        print("-")
        input("Press Enter to install... ")

        print("-")
        print("- Installing...")

        # Make sure pip is installed
        if importlib.util.find_spec("pip") is None:
            print( "-")
            print(f"- {COLORS.DARK_RED}FATAL ERROR{COLORS.RESET} - The pip package installer was not found.")
            print( "-")
            print( "- Try reinstalling python, choose Customize installation and")
            print( "- make sure to tick the \"pip\" option.")
            print( "-")

            input("Press Enter to exit... ")
            exit()

        # Install the dependencies (closes the program automatically after the installation)
        sys.argv = ["pip", "install"] + [dependency["name_pip"] for dependency in dependencies_missing]

        try:
            runpy.run_module("pip", run_name="__main__")

        except Exception as e:
            print( "-")
            print(f"- {COLORS.DARK_RED}FATAL ERROR{COLORS.RESET} - Error while trying to install the dependencies:")
            print(e)
            print( "-")
            print( "- Try reinstalling python, do not choose \"Install for all users\".")
            print( "-")

            input("Press Enter to exit... ")
            exit()


# Run the check when imported
if __name__.endswith("dependency_check"):
    dependency_check_on_import()
