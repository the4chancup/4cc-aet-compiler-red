import os
import sys
import shutil
import logging


from .utils import cpk
from .utils.pausing import pause
from .utils.dpfl_scan import dpfl_scan
from .utils.zlib_plus import tryDecompress
from .utils.logging_tools import logger_stop
from .utils.file_management import file_critical_check


# Find the file in the cpk
def cpk_file_extract(cpk_path, file_source_path):

    file_contents = None

    # Create a cpk reader object and open the cpk
    cpk_search = cpk.CpkReader()
    cpk_search.open(cpk_path)

    # Search through the files
    for file in cpk_search.files:

        if file.name == file_source_path:

            # Read the file contents
            file_contents = cpk_search.readFile(file)

            break

    cpk_search.close()

    return file_contents


def files_fetch_from_cpks(file_info_list, cpk_names_list, fetch=True):

    # Read the necessary parameters
    pes_folder_path = os.environ.get('PES_FOLDER_PATH', 'unknown')
    cpk_name = os.environ.get('CPK_NAME', 'unknown')

    pes_download_path = os.path.join(pes_folder_path, "download")
    dpfl_path = os.path.join(pes_download_path, "DpFileList.bin")

    file_found_all = False

    if os.path.exists(dpfl_path):

        dpfl_list = dpfl_scan(dpfl_path)

        # List with every cpk file in the dpfl, in reverse alphabetical order
        cpk_file_list = sorted(dpfl_list, reverse=True)

        file_found_all = True

        for file_info in file_info_list:

            cpk_name_found = False

            for cpk_file in cpk_file_list:

                # Skip the cpks until we have found and skipped the cpk we are about to pack
                if not cpk_name_found:
                    if cpk_file == cpk_name + ".cpk":
                        cpk_name_found = True
                    continue

                # If the cpk name contains any of the names in the list, search for the corresponding file
                if any(x in cpk_file for x in cpk_names_list):

                    cpk_path = os.path.join(pes_download_path, cpk_file)

                    file_data = cpk_file_extract(cpk_path, file_info['source_path'])

                    if file_data:
                        if fetch:

                            print(f"- {os.path.basename(file_info['source_path'])} found in the cpk {os.path.basename(cpk_path)}")

                            # Save the file to the corresponding destination path after unzlibbing it if needed
                            with open(file_info['destination_path'], "wb") as file:
                                file.write(tryDecompress(file_data))

                        break
            else:
                file_found_all = False

    if fetch and not file_found_all:

        # Copy any missing files from the fallback folder
        for file_info in file_info_list:

            if os.path.exists(file_info['destination_path']):
                continue

            file_fallback_path = os.path.join(os.path.dirname(os.path.dirname(file_info['destination_path'])), os.path.basename(file_info['destination_path']))
            file_critical_check(file_fallback_path)

            shutil.copy(file_fallback_path, file_info['destination_path'])

            print(f"- {os.path.basename(file_info['source_path'])} not found in any cpks, copied from the fallback folder")

    return file_found_all


def pes_download_path_check(settings_name, pes_download_path):
    '''Check the PES download folder'''

    if os.path.exists(pes_download_path):
        return

    logging.critical("-")
    logging.critical("- FATAL ERROR - PES download folder not found")
    logging.critical("-")
    logging.critical("- Please set the correct path to the main PES folder")
    logging.critical("- in the settings file and start again")

    # Stop the loggers
    logger_stop()

    print("-")
    if sys.platform == "win32":
        pause("Press any key to open the settings file and exit... ")
        # Open the settings file in an external text editor
        os.startfile(settings_name)
    else:
        pause("Press any key to exit... ")

    # Exit the script
    exit()
