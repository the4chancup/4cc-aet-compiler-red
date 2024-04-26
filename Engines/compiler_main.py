## Main script for the compiler
import os
import sys
import ctypes
import logging

from python.dependency_check import dependency_check_on_import as dependency_check_on_import
from python.admin_check import admin_check
from python.update_check import update_check
from python.settings_init import settings_init
from python.extracted_from_exports import extracted_from_exports
from python.contents_from_extracted import contents_from_extracted
from python.patches_from_contents import patches_from_contents


APP_OWNER = "the4chancup"
APP_NAME = "4cc-aet-compiler-red"
APP_VERSION_MAJOR = 3
APP_VERSION_MINOR = 1
APP_VERSION_PATCH = 0


class ColorFilter(logging.Filter):
    """
    This is a filter which colorizes the words "ERROR" and "Warning".

    "ERROR" gets turned into "\033[31mERROR\033[0m"
    "Warning" gets turned into "\033[33mWarning\033[0m"
    """

    def filter(self, record):
        ERROR_STRING = "ERROR"
        ERROR_STRING_COLORED = "\033[31mERROR\033[0m"
        record.msg = record.msg.replace(ERROR_STRING, ERROR_STRING_COLORED)

        WARNING_STRING = "Warning"
        WARNING_STRING_COLORED = "\033[33mWarning\033[0m"
        record.msg = record.msg.replace(WARNING_STRING, WARNING_STRING_COLORED)

        return True


def admin_request(run_type):

    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except PermissionError:
            return False

    if not is_admin():

        print('-')
        print('-')
        print('Your PES is installed in a system folder and Move Cpks mode is enabled.')
        print('Administrative privileges are needed to move the cpk directly to the download folder.')
        print('-')

        warning_path = os.path.join("Engines","admin_warned.txt")

        if not os.path.exists(warning_path):
            print('Either accept the incoming request or disable Move Cpks mode in the settings file.')
            print('-')

            input('Press Enter to continue...')

            with open(warning_path, 'w') as f:
                f.write('This file tells the compiler that you know why the request for admin privileges is needed.')

        # Prepare the path to the compiler_run.bat file in the same folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        compiler_run_path = os.path.join(current_dir, "compiler_run.bat")

        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", compiler_run_path, run_type, None, 1)

        # Exit the program
        sys.exit()


def intro_print():
    if sys.platform == "win32":
        os.system("color")
    version_string = f'{APP_VERSION_MAJOR}.{APP_VERSION_MINOR}.{APP_VERSION_PATCH}'
    print('-')
    print('-')
    print('- 4cc aet compiler ' + '\033[91m' + 'Red' + '\033[0m' + f' {version_string}')
    print('-')
    print('-')


def log_store(log_name):
    if os.path.exists(log_name):
        log_name_old = log_name + ".old"
        if os.path.exists(log_name_old):
            os.remove(log_name_old)
        try:
            os.rename(log_name, log_name_old)
        except OSError:
            print(f"- An error occurred while trying to rename the {log_name} file")
            print("- Please check if it's open in another program")
            print("-")
            input("Press Enter to continue after checking...")
            os.rename(log_name, log_name_old)


def logger_init(__name__):

    # If an issues log file already exists, add .old to it
    ISSUES_LOG_NAME = "issues.log"
    log_store(ISSUES_LOG_NAME)

    # Create a file handler which will only create a file when a WARNING or higher occurs
    file_handler = logging.FileHandler(ISSUES_LOG_NAME, delay=True)
    file_handler.setLevel(logging.WARNING)

    # Add it to the root logger
    logging.getLogger().addHandler(file_handler)

    # Create a stream handler for outputting colored errors to stderr
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.ERROR)
    stream_handler.addFilter(ColorFilter())

    # Add it to the root logger
    logging.getLogger().addHandler(stream_handler)


    # If an error log file already exists, add .old to it
    ERROR_LOG_NAME = "error.log"
    log_store(ERROR_LOG_NAME)

    # Create a logger
    logger = logging.getLogger(__name__)

    # Create a file handler which will only create a file when an exception occurs
    handler = logging.FileHandler(ERROR_LOG_NAME, delay=True)

    # Create a formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)-15s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger


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
    move_cpks = int(os.environ.get('MOVE_CPKS', '0'))
    pes_folder_path = os.environ.get('PES_FOLDER_PATH', 'unknown')
    run_pes = int(os.environ.get('RUN_PES', '0'))
    admin_mode = int(os.environ.get('ADMIN_MODE', '0'))
    updates_check = int(os.environ.get('UPDATES_CHECK', '1'))

    pes_download_path = os.path.join(pes_folder_path, "download")

    # Check for updates
    if updates_check and sys.platform == "win32":
        update_check(APP_OWNER, APP_NAME, APP_VERSION_MAJOR, APP_VERSION_MINOR, APP_VERSION_PATCH)

    # If patches_from_contents_run is active and move_cpks mode is enabled
    if patches_from_contents_run and move_cpks:

        # Check the PES download folder
        if not os.path.exists(pes_download_path):
            print("-")
            print("-")
            print("- PES download folder not found.")
            print("- Please set its correct path in the settings file and start again.")
            print("-")
            print("-")
            input("Press Enter to continue...")

            if sys.platform == "win32":
                # Open the settings file in an external text editor
                os.startfile(settings_name)

            # Exit the script
            sys.exit()

        # If admin mode has been forced or is needed
        if sys.platform == "win32" and (admin_mode or admin_check(pes_download_path)):
            # Ask for admin permissions if not obtained yet
            admin_request(run_type)

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
    logging.shutdown()

    # Exit the script
    if not (patches_from_contents_run and run_pes) or os.path.exists("issues.log"):
        input("Press Enter to exit...")


if __name__ == "__main__":

    intro_print()

    # Enable the advanced traceback handler
    from traceback_with_variables import activate_by_import as activate_by_import
    from traceback_with_variables import printing_exc, LoggerAsFile

    # Enable the exception logger
    logger = logger_init(__name__)

    # Check if an argument has been passed and its value is between 0 and 3
    if len(sys.argv) > 1 and sys.argv[1] in ["0", "1", "2", "3"]:
        run_type = sys.argv[1]
    else:
        run_type = run_type_request()

    # Run the main function with the exception logger
    with printing_exc(file_=LoggerAsFile(logger)):
        main(run_type)
