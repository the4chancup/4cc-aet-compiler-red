import sys
import runpy
import importlib.util


# Check if the dependencies are installed
def dependency_check_on_import():

    # Prepare a list of dependencies as dictionaries with name and name_pip
    dependencies = [
        {"name": "py7zr",                    "name_pip": "py7zr"},
        {"name": "requests",                 "name_pip": "requests"},
        {"name": "commentedconfigparser",    "name_pip": "commented-configparser"},
        {"name": "traceback_with_variables", "name_pip": "traceback_with_variables"},
    ]

    dependencies_missing = []

    for dependency in dependencies:
        if importlib.util.find_spec(dependency["name"]) is None:
            # Add any missing dependencies to the list
            dependencies_missing.append(dependency["name_pip"])

    if dependencies_missing:

        print("-")
        print("- The following dependencies were not found:")
        # List the missing dependencies, one per line
        for dependency in dependencies_missing:
            print(f"- \"{dependency}\"")

        print("-")
        print("- They will be installed now (or you can close the program now and install them manually).")
        print("- Once the installation is complete, the program will be closed automatically.")
        print("- Please run it again afterwards.")
        print("-")
        input("Press Enter to install... ")

        print("-")
        print("- Installing...")

        # Install the dependencies (closes the program automatically after the installation)
        sys.argv = ["pip", "install"] + dependencies_missing
        runpy.run_module("pip", run_name="__main__")


# Run the check when imported
if __name__.endswith("dependency_check"):
    dependency_check_on_import()
