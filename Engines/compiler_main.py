#! /usr/bin/env python3
import os
import sys
import logging

# Error handler for library errors
def handle_library_error(e):
    print("-")
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

# Modules needed for self healing
try:
    if "__compiled__" not in globals():
        # If the script is not compiled, check for dependencies and allow self healing
        from python.dependency_check import dependency_check_on_import as dependency_check_on_import
        from python.lib.utils.file_management import module_recover
    from python.lib.utils.updating import update_check
    from python.lib.utils.APP_DATA import (
        APP_OWNER,
        APP_NAME,
        APP_VERSION_MAJOR,
        APP_VERSION_MINOR,
        APP_VERSION_PATCH,
        APP_VERSION_DEV as APP_VERSION_DEV,
    )
except ImportError as e:
    handle_library_error(e)

# Modules which can be self healed
while True:
    try:
        from python.log_username_clean import username_clean_from_logs
        from python.extracted_from_exports import extracted_from_exports
        from python.contents_from_extracted import contents_from_extracted
        from python.patches_from_contents import patches_from_contents
        from python.lib.cpk_tools import pes_download_path_check, cpk_name_check
        from python.lib.utils.admin_tools import admin_check, admin_request
        from python.lib.utils.app_tools import app_title, pes_title
        from python.lib.utils.logging_tools import logger_init, logger_stop
        from python.lib.utils.pausing import pause
        from python.lib.utils.settings_management import settings_init, first_run_wizard
        from python.lib.utils.FILE_INFO import (
            SETTINGS_PATH,
            RUN_BATCH_PATH,
            FIRST_RUN_DONE_PATH,
        )
    except ImportError as e:
        if "__compiled__" not in globals():
            # If the script is not compiled, try to self heal
            module_recover(e)
        else:
            # It should not be possible to lack a library file if the script is compiled,
            # but if it ever happens, show a library error
            handle_library_error(e)
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
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))

    # Check the running type
    all_in_one = (run_type == "0")
    extracted_from_exports_run = (run_type == "1" or all_in_one)
    contents_from_extracted_run = (run_type == "2" or all_in_one)
    patches_from_contents_run = (run_type == "3" or all_in_one)

    # Load the settings into the environment
    settings_init()

    # Check for updates
    updates_check = int(os.environ.get('UPDATES_CHECK', '1'))
    if updates_check:
        update_check(APP_OWNER, APP_NAME, APP_VERSION_MAJOR, APP_VERSION_MINOR, APP_VERSION_PATCH)

    # Start the first run wizard on the first run
    if not os.path.exists(FIRST_RUN_DONE_PATH):
        first_run_wizard()

    # Read the necessary parameters
    pes_version = int(os.environ.get('PES_VERSION', '19'))
    cpk_name = os.environ.get('CPK_NAME', '4cc_90_test')
    move_cpks = int(os.environ.get('MOVE_CPKS', '0'))
    pes_folder_path = os.environ.get('PES_FOLDER_PATH', 'unknown')
    run_pes = int(os.environ.get('RUN_PES', '0'))
    admin_mode = int(os.environ.get('ADMIN_MODE', '0'))
    pes_download_path = os.path.join(pes_folder_path, "download")

    # If patches_from_contents_run is active and move_cpks mode is enabled
    if patches_from_contents_run and move_cpks:

        # Check the PES download folder
        pes_download_path_check(SETTINGS_PATH, pes_download_path)

        # Check if the cpk name is listed on the dpfl file
        cpk_name_check(SETTINGS_PATH, cpk_name, pes_download_path)

        # If admin mode has been forced or is needed
        admin_needed = admin_mode or admin_check(pes_download_path)

        if sys.platform == "win32" and admin_needed:

            # Ask for admin permissions if not obtained yet
            admin_request(RUN_BATCH_PATH, run_type)

    elif patches_from_contents_run:

        # Check if the cpk name is listed on the dpfl file
        cpk_name_check(SETTINGS_PATH, cpk_name, pes_download_path, compulsory=False)

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

    if len(sys.argv) > 1 and sys.argv[1] == "-1":
        # Run the log cleaner to remove the username from the logs
        username_clean_from_logs()
        sys.exit()

    if sys.platform == "win32":

        # Set the console title
        os.system("title " + app_title(colorize=False))

    print("-")
    print("-")
    print("- " + app_title())
    print("-")
    print("-")

    # Enable the advanced traceback handler
    from rich.traceback import install
    install(show_locals=True)

    # Enable the loggers
    logger_init()

    # Check if an argument has been passed and its value is between 0 and 3
    if len(sys.argv) > 1 and sys.argv[1] in ["0", "1", "2", "3"]:
        run_type = sys.argv[1]
    else:
        run_type = run_type_request()

    # Run the main function
    main(run_type)
