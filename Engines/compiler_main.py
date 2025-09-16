#! /usr/bin/env python3
import os
import sys
import logging

# Modules needed for self healing
try:
    from python.dependency_check import dependency_check_on_import as dependency_check_on_import
    from python.lib.utils.APP_DATA import (
        APP_OWNER,
        APP_NAME,
        APP_VERSION_MAJOR,
        APP_VERSION_MINOR,
        APP_VERSION_PATCH,
        APP_VERSION_DEV as APP_VERSION_DEV,
    )
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
        from python.lib.utils.FILE_INFO import (
            SETTINGS_PATH,
            RUN_BATCH_PATH,
        )
        from python.lib.utils.app_tools import app_title, pes_title
        from python.lib.utils.logging_tools import logger_init, logger_stop
        from python.lib.utils.settings_management import settings_init
        from python.lib.utils.admin_tools import admin_check, admin_request
        from python.lib.utils.pausing import pause
        from python.lib.cpk_tools import pes_download_path_check, cpk_name_check
        from python.extracted_from_exports import extracted_from_exports
        from python.contents_from_extracted import contents_from_extracted
        from python.patches_from_contents import patches_from_contents
    except ImportError as e:
        module_recover(e)
    else:
        break


def run_type_request():
    print("Usage:")
    print("  compiler_main <run type>")
    print("run type:")
    print("  0                         all-in-one mode, runs every main step")
    print("  1                         [main] extracted_from_exports mode, unpacks and checks exports")
    print("  2                         [main] contents_from_extracted mode, prepares the contents folder")
    print("  3                         [main] patches_from_contents mode, packs the patches")
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
    extracted_from_exports_run = (run_type == "1" or all_in_one)
    contents_from_extracted_run = (run_type == "2" or all_in_one)
    patches_from_contents_run = (run_type == "3" or all_in_one)

    # Load the settings into the environment
    settings_init()

    # Read the necessary parameters
    pes_version = int(os.environ.get('PES_VERSION', '19'))
    cpk_name = os.environ.get('CPK_NAME', '4cc_90_test')
    move_cpks = int(os.environ.get('MOVE_CPKS', '0'))
    pes_folder_path = os.environ.get('PES_FOLDER_PATH', 'unknown')
    run_pes = int(os.environ.get('RUN_PES', '0'))
    admin_mode = int(os.environ.get('ADMIN_MODE', '0'))
    updates_check = int(os.environ.get('UPDATES_CHECK', '1'))

    cpk_used_name = cpk_name
    pes_download_path = os.path.join(pes_folder_path, "download")

    # Check for updates
    if updates_check:
        update_check(APP_OWNER, APP_NAME, APP_VERSION_MAJOR, APP_VERSION_MINOR, APP_VERSION_PATCH)

    # If patches_from_contents_run is active and move_cpks mode is enabled
    if patches_from_contents_run and move_cpks:

        # Check the PES download folder
        pes_download_path_check(SETTINGS_PATH, pes_download_path)

        # Check if the cpk name is listed on the dpfl file
        cpk_name_check(SETTINGS_PATH, cpk_used_name, pes_download_path)

        # If admin mode has been forced or is needed
        admin_needed = admin_mode or admin_check(pes_download_path)

        if sys.platform == "win32" and admin_needed:

            # Ask for admin permissions if not obtained yet
            admin_request(RUN_BATCH_PATH, run_type)

    elif patches_from_contents_run:

        # Check if the cpk name is listed on the dpfl file
        cpk_name_check(SETTINGS_PATH, cpk_used_name, pes_download_path, compulsory=False)

    # Save the all-in-one mode
    os.environ['ALL_IN_ONE'] = str(int(all_in_one))

    print("-")
    print("- Compiling for " + pes_title(pes_version) + "...")
    print("-")

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

    # Pause the script before exiting, unless PES has been launched
    exit_pause_skip = (run_pes and patches_from_contents_run)

    if not exit_pause_skip:
        pause("Press any key to exit... ", print_hyphen=False)


if __name__ == "__main__":

    if sys.platform == "win32":

        # Set the console title
        os.system("title " + app_title(colorize=False))

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
