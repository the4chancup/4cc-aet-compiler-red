import os
import shutil

from .utils import cpk
from .utils.dpfl_scan import dpfl_scan
from .utils.zlib_plus import tryDecompress


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
            for cpk_file in cpk_file_list:

                # If the cpk name contains any of the names in the list, and is not
                # the cpk we are about to pack, search for the corresponding file
                if any(x in cpk_file for x in cpk_names_list) and (cpk_file != cpk_name):

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
            if not os.path.exists(file_info['destination_path']):

                file_fallback_path = os.path.join(os.path.dirname(os.path.dirname(file_info['destination_path'])), os.path.basename(file_info['destination_path']))

                shutil.copy(file_fallback_path, file_info['destination_path'])

                print(f"- {os.path.basename(file_info['source_path'])} not found in any cpks, copied from the fallback folder")

    return file_found_all
