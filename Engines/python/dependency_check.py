import sys
import runpy
import subprocess
import importlib.util
import importlib.metadata

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
    dependencies: list[dict[str, str]] = [
        {
            "name_package": "py7zr",
            "version":      "any",
            "name_pip":     "py7zr",
            "name_user":    "Py7zr (7z extractor)",
        },
        {
            "name_package": "requests",
            "version":      "any",
            "name_pip":     "requests",
            "name_user":    "Requests (HTTP library)",
        },
        {
            "name_package": "commentedconfigparser",
            "version":      "any",
            "name_pip":     "commented-configparser",
            "name_user":    "Commented Config Parser (config file parser)",
        },
        {
            "name_package": "rich",
            "version":      "any",
            "name_pip":     "rich",
            "name_user":    "Rich (rich text console output)",
        },
    ]

    dependencies_missing: list[dict[str, str]] = []

    for dependency in dependencies:
        spec = importlib.util.find_spec(dependency["name_package"])
        if spec is None:
            # Add any missing dependencies to the list
            dependencies_missing.append(dependency)
            continue

        # Check version constraints if not "any"
        if dependency["version"] != "any":
            try:
                installed_version = importlib.metadata.version(dependency["name_pip"])
            except importlib.metadata.PackageNotFoundError:
                dependencies_missing.append(dependency)
                continue

            if (
                (dependency["version"].startswith("~=") and
                not installed_version.startswith(dependency["version"][2:-1])) or
                (dependency["version"].startswith("==") and
                not installed_version.startswith(dependency["version"][2:]))
            ):
                dependencies_missing.append(dependency)
                continue

    if dependencies_missing:

        print("-")
        print("- The following dependencies were not found:")
        # List the missing dependencies, one per line
        for dependency in dependencies_missing:
            if dependency["version"].startswith("~="):
                version_string = f" (version {dependency['version'][2:-2]})"
            elif dependency["version"].startswith("=="):
                version_string = f" (version {dependency['version'][2:]})"
            else:
                version_string = ""
            print(f"- {dependency['name_user']}{version_string}")

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
        pip_packages = []
        for dependency in dependencies_missing:
            if dependency["version"] == "any":
                pip_packages.append(dependency["name_pip"])
            else:
                pip_packages.append(f"{dependency['name_pip']}{dependency['version']}")

        sys.argv = ["pip", "install"] + pip_packages

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
