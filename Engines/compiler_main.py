## Main script for the compiler
import os
import sys
import logging

# Modules needed for self healing
try:
    from python.dependency_check import dependency_check_on_import as dependency_check_on_import
    from python.lib.utils import APP_DATA
    from python.lib.utils.updating import update_check
    from python.lib.utils.file_management import module_recover
except ImportError as e:
    print("- FATAL ERROR - Library file not found:")
    print(e)
    print("-")
    print("- Please grab a clean compiler folder")
    # Log to file
    logging.basicConfig(filename="issues.log", level=logging.CRITICAL, filemode='w', format="%(message)s")
    logging.critical("Library file not found, please grab a clean compiler folder.")
    logging.critical(e)

    print("-")
    input("Press Enter to exit... ")

    exit()

# Modules which can be self healed
while True:
    try:
        from python.lib.utils.app_tools import app_title
        from python.lib.utils.logging_tools import logger_init
        from python.lib.utils.logging_tools import logger_stop
        from python.lib.utils.settings_management import settings_init
        from python.lib.utils.admin_tools import admin_check
        from python.lib.utils.admin_tools import admin_request
        from python.lib.utils.pausing import pause
        from python.lib.cpk_tools import pes_download_path_check
        from python.lib.cpk_tools import cpk_name_check
        from python.extracted_from_exports import extracted_from_exports
        from python.contents_from_extracted import contents_from_extracted
        from python.patches_from_contents import patches_from_contents
    except ImportError as e:
        module_recover(e)
    else:
        break


APP_OWNER = APP_DATA.OWNER
APP_NAME = APP_DATA.NAME
APP_VERSION_MAJOR = APP_DATA.VERSION_MAJOR
APP_VERSION_MINOR = APP_DATA.VERSION_MINOR
APP_VERSION_PATCH = APP_DATA.VERSION_PATCH
APP_VERSION_DEV = APP_DATA.VERSION_DEV


def run_type_request():
    print("Usage:")
    print("  compiler_main <run type>")
    print("run type:")
    print("  0                         all-in-one mode, runs every step")
    print("  1                         extracted_from_exports mode, unpacks and checks exports")
    print("  2                         contents_from_extracted mode, prepares the contents folder")
    print("  3                         patches_from_contents mode, packs the patches")
    print("")

    # Ask the user for a run type, read a single character input
    run_type = input("You can also choose a type now: ")

    # Check if run_type is between 0 and 3, ask again otherwise
    while run_type not in ["0", "1", "2", "3"]:
        print("Invalid run type, please try again or close the program.")
        print("")
        run_type = input("Choose a type: ")

    return run_type


def main(run_type):

    # Set the working folder to the parent of the folder of this script
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Check the running type
    all_in_one = (run_type == "0")
    extracted_from_exports_run = (run_type == "0" or run_type == "1")
    contents_from_extracted_run = (run_type == "0" or run_type == "2")
    patches_from_contents_run = (run_type == "0" or run_type == "3")

    # Load the settings into the environment
    settings_name = "settings.ini"
    settings_init(settings_name)

    # Read the necessary parameters
    cpk_name = os.environ.get('CPK_NAME', 'unknown')
    move_cpks = int(os.environ.get('MOVE_CPKS', '0'))
    pes_folder_path = os.environ.get('PES_FOLDER_PATH', 'unknown')
    run_pes = int(os.environ.get('RUN_PES', '0'))
    pause_on_error = int(os.environ.get('PAUSE_ON_ERROR', '1'))
    admin_mode = int(os.environ.get('ADMIN_MODE', '0'))
    updates_check = int(os.environ.get('UPDATES_CHECK', '1'))

    pes_download_path = os.path.join(pes_folder_path, "download")

    # Check for updates
    if updates_check:
        update_check(APP_OWNER, APP_NAME, APP_VERSION_MAJOR, APP_VERSION_MINOR, APP_VERSION_PATCH)

    # If patches_from_contents_run is active and move_cpks mode is enabled
    if patches_from_contents_run and move_cpks:

        # Check the PES download folder
        pes_download_path_check(settings_name, pes_download_path)

        # Check if the cpk name is listed on the dpfl file
        cpk_name_check(settings_name, cpk_name, pes_download_path)

        # If admin mode has been forced or is needed
        admin_needed = admin_mode or admin_check(pes_download_path)

        if sys.platform == "win32" and admin_needed:

            # Prepare the path to the compiler_run.bat file in the same folder
            current_dir = os.path.dirname(os.path.abspath(__file__))
            compiler_run_path = os.path.join(current_dir, "compiler_run.bat")

            # Ask for admin permissions if not obtained yet
            admin_request(compiler_run_path, run_type)

    # Save the all-in-one mode
    os.environ['ALL_IN_ONE'] = str(int(all_in_one))

    # Invoke the export extractor
    if extracted_from_exports_run:
        extracted_from_exports()

    # Invoke the contents packer
    if contents_from_extracted_run:
        contents_from_extracted()

    # Invoke the cpk packer
    if patches_from_contents_run:
        patches_from_contents()

    # Stop the loggers
    logger_stop()

    # Pause the script before exiting, unless PES is about to run
    # Pause it anyway if there's a log file and Pause on Error is enabled
    exit_pause_skip = (
        run_pes and
        patches_from_contents_run and
        not (os.path.exists("issues.log") and pause_on_error)
    )

    if not exit_pause_skip:
        pause("Press any key to exit... ")


if __name__ == "__main__":

    if sys.platform == "win32":

        # Set the console title
        os.system("title " + app_title(colorize=False))

        # Enable color on Windows
        if "NO_COLOR" not in os.environ:
            os.system("color")

    print("-")
    print("-")
    print("- " + app_title())
    print("-")
    print("-")

    # Enable the advanced traceback handler
    from traceback_with_variables import activate_by_import as activate_by_import
    from traceback_with_variables import printing_exc, LoggerAsFile

    # Enable the loggers
    logger = logger_init(__name__)

    # Check if an argument has been passed and its value is between 0 and 3
    if len(sys.argv) > 1 and sys.argv[1] in ["0", "1", "2", "3"]:
        run_type = sys.argv[1]
    else:
        run_type = run_type_request()

    # Run the main function with the exception logger
    with printing_exc(file_=LoggerAsFile(logger)):
        main(run_type)
