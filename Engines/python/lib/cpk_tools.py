import os
import shutil

from .utils import cpk
from .utils.dpfl_scan import dpfl_scan
from .utils.zlib_plus import tryDecompress


# Find the UniColor bin file in the cpk
def cpk_file_extract(cpk_path, file_source_path):
    
    file_contents = None
    
    # Create a cpk reader object and open the cpk
    cpk_search = cpk.CpkReader()
    cpk_search.open(cpk_path)
    
    # Search through the files
    for file in cpk_search.files:
        
        if file.name == file_source_path:
            
            print(f"- {os.path.basename(file_source_path)} found in the cpk {os.path.basename(cpk_path)}")
            
            # Read the file contents
            file_contents = cpk_search.readFile(file)
            
            break
    
    cpk_search.close()
    
    return file_contents


def files_fetch_from_cpks(file_info_list):
    
    pes_folder_path = os.environ.get('PES_FOLDER_PATH', 'unknown')
    pes_download_path = os.path.join(pes_folder_path, "download")
    dpfl_path = os.path.join(pes_download_path, "DpFileList.bin")

    if os.path.exists(dpfl_path):
        
        dpfl_list = dpfl_scan(dpfl_path)

        # List with every cpk file in the dpfl, in reverse alphabetical order
        cpk_file_list = sorted(dpfl_list, reverse=True)

        for file_info in file_info_list:
            for cpk_file in cpk_file_list:
                
                # If the cpk name contains "midcup" or "bins", search for the corresponding bin file
                if "midcup" in cpk_file or "bins" in cpk_file:
                    
                    cpk_path = os.path.join(pes_download_path, cpk_file)
                
                    bin_data = cpk_file_extract(cpk_path, file_info['source_path'])
                    
                    if bin_data:
                        # Save the bin file to the corresponding bin destination path after unzlibbing it if needed
                        with open(file_info['destination_path'], "wb") as bin_file:
                            bin_file.write(tryDecompress(bin_data))
                    
                        break

    # Copy any missing bin files from the fallback folder
    for file_info in file_info_list:
        if not os.path.exists(file_info['destination_path']):
            
            bin_fallback_path = os.path.join(os.path.dirname(os.path.dirname(file_info['destination_path'])), os.path.basename(file_info['destination_path']))
            
            shutil.copy(bin_fallback_path, file_info['destination_path'])
            
            print(f"- {os.path.basename(file_info['source_path'])} not found in any cpks, copied from the fallback folder")
