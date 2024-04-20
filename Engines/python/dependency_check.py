import sys
import runpy
import importlib
import importlib.util


# Check if the dependencies are installed
def dependency_check():
    # Prepare a list of dependencies
    dependencies = [
        "py7zr",
        "traceback_with_variables",
    ]
    if sys.platform == "win32":
        dependencies.append("requests")

    try:
        for dependency in dependencies:
            importlib.import_module(dependency)
    except ImportError:
        print("- The following new dependencies were not found:")
        # List the missing dependencies, one per line
        dependencies_missing = [f"{dependency}" for dependency in dependencies if not importlib.util.find_spec(dependency)]
        for dependency in dependencies_missing:
            print(f"- \"{dependency}\"")
        print("-")

        print("- They will be installed now (or you can close the program now and install them manually).")
        print("- Once the installation is complete, the program will be closed automatically.")
        print("- Please run it again afterwards.")
        print("-")
        input("Press Enter to install...")

        print("- Installing...")

        # Install the dependencies (closes the program automatically after the installation)
        sys.argv = ["pip", "install"] + dependencies_missing
        runpy.run_module("pip", run_name="__main__")


# Run the module when imported
if __name__.endswith("dependency_check"):
    dependency_check()
