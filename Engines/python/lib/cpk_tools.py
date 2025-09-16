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
def cpk_file_search(cpk_path, file_source_path, fetch=False):

    file_contents = None

    # Create a cpk reader object and open the cpk
    cpk_search = cpk.CpkReader()
    cpk_search.open(cpk_path)

    # Search through the files
    for file in cpk_search.files:

        if file.name == file_source_path:

            if fetch:
                # Read the file contents
                file_contents = cpk_search.readFile(file)
            else:
                file_contents = file.name

            break

    cpk_search.close()

    return file_contents


def files_fetch_from_cpks(file_info_list, cpk_names_list, fetch=True):

    # Read the necessary parameters
    pes_folder_path = os.environ.get('PES_FOLDER_PATH', 'unknown')

    multicpk_mode = int(os.environ.get('MULTICPK_MODE', '0'))
    cpk_name_singlecpk = os.environ.get('CPK_NAME', 'unknown')
    cpk_name_multicpk = os.environ.get('BINS_CPK_NAME', 'unknown')

    pes_download_path = os.path.join(pes_folder_path, "download")
    dpfl_path = os.path.join(pes_download_path, "DpFileList.bin")
    cpk_name = cpk_name_singlecpk if not multicpk_mode else cpk_name_multicpk

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

                    file_data = cpk_file_search(cpk_path, file_info['source_path'], fetch)

                    if file_data is not None:
                        if fetch:

                            print(f"- {os.path.basename(file_info['source_path'])} found in {os.path.basename(cpk_path)}")

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

            file_critical_check(file_info['fallback_path'])
            shutil.copy(file_info['fallback_path'], file_info['destination_path'])

            print(f"- {os.path.basename(file_info['source_path'])} not found in any cpks, copied from the fallback folder")

    return file_found_all


def pes_download_path_check(settings_name, pes_download_path):
    '''Check the PES download folder'''

    if os.path.exists(pes_download_path):
        return

    logging.critical( "-")
    logging.critical( "- FATAL ERROR - PES download folder not found")
    logging.critical(f"- Path set: {pes_download_path}")
    logging.critical( "-")
    logging.critical( "- Please set the correct path to the main PES folder")
    logging.critical( "- in the settings file and start again")

    # Stop the loggers
    logger_stop()

    if sys.platform == "win32":
        pause("Press any key to open the settings file and exit... ", force=True)
        # Open the settings file in an external text editor
        os.startfile(settings_name)
    else:
        pause("Press any key to exit... ", force=True)

    # Exit the script
    exit()


def cpk_name_check(settings_name, cpk_name, pes_download_path, compulsory=True):
    '''Check if the cpk name is listed on the dpfl file'''

    dpfl_path = os.path.join(pes_download_path, "DpFileList.bin")

    if not os.path.exists(dpfl_path):
        if not compulsory:
            return

        logging.critical( "-")
        logging.critical( "- FATAL ERROR - DpFileList file not found in the PES download folder")
        logging.critical(f"- Path: {dpfl_path}")
        logging.critical( "-")
        logging.critical( "- Please make sure there is a DpFileList file in the PES download folder")
        logging.critical( "- and start again")

        pause("Press any key to exit... ", force=True)

        exit()

    dpfl_list = dpfl_scan(dpfl_path)

    if (cpk_name + ".cpk") in dpfl_list:
        return

    if not compulsory:
        logging.error( "-")
        logging.error( "- ERROR - CPK name not listed on the DpFileList file")
        logging.error(f"- CPK name: {cpk_name}")
        logging.error( "-")
        logging.error( "- PES probably won't load this CPK if you move it to the PES download folder")
        logging.error( "- Changing the CPK name in the settings file back to the default name is")
        logging.error( "- recommended")
        pause()
        return

    logging.critical( "-")
    logging.critical( "- FATAL ERROR - CPK name not listed on the DpFileList file")
    logging.critical(f"- CPK name: {cpk_name}")
    logging.critical( "-")
    logging.critical( "- Please set a listed CPK name in the settings file and start again")
    logging.critical( "- Or, if you really want to use this CPK name, disable Move Cpks instead")

    # Stop the loggers
    logger_stop()

    pause("Press any key to show the list of CPKs on the DpFileList... ", force=True)
    print("-")
    for cpk_listed in dpfl_list:
        print("- " + cpk_listed[0:-4])

    if sys.platform == "win32":
        pause("Press any key to open the settings file and exit... ", force=True)
        # Open the settings file in an external text editor
        os.startfile(settings_name)
    else:
        pause("Press any key to exit... ", force=True)

    # Exit the script
    exit()
