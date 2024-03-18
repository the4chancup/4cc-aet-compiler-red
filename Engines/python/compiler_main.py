## Main script for the compiler
import os
import sys
import ctypes
from lib.admin_check import admin_check
from .extracted_from_exports import extracted_from_exports
from .contents_from_extracted import contents_from_extracted
from .patches_from_contents import patches_from_contents


# Read the necessary parameters
move_cpks = int(os.environ.get('MOVE_CPKS', '0'))
pes_download_folder_location = os.environ.get('PES_DOWNLOAD_FOLDER_LOCATION', 'unknown')
admin_mode = int(os.environ.get('ADMIN_MODE', '0'))


def admin_request():

    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
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
  
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


def intro_print():
    if sys.platform == "win32":
        os.system("color")
    print('-')
    print('-')
    print('- 4cc aet compiler ' + '\033[91m' + 'Red' + '\033[0m')
    print('-')
    print('-')


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
        print("Invalid run type, please try again")
        print("")
        run_type = input("Choose a type: ")
        
    return run_type


def main(run_type):
    
    # Check the running type
    all_in_one = (run_type == "0")
    extracted_from_exports_run = (run_type == "0" or run_type == "1")
    contents_from_extracted_run = (run_type == "0" or run_type == "2")
    patches_from_contents_run = (run_type == "0" or run_type == "3")
    
    # If move_cpks mode is enabled
    if move_cpks == "1":

        # Check the PES download folder
        if not os.path.exists(pes_download_folder_location):
            print("-")
            print("-")
            print("- PES download folder not found.")
            print("- Please set its correct path in the settings file and start again.")
            print("- The script will restart automatically after you close notepad.")
            print("-")
            print("-")
            input("Press Enter to continue...")

            # Open settings.txt in an external text editor
            os.startfile("settings.txt")
            
            # Exit the script
            sys.exit()

        # If admin mode has been forced or is needed
        if sys.platform == "win32" and (admin_mode or admin_check(pes_download_folder_location)):
            # Ask for admin permissions if not obtained yet
            admin_request()
        
        
        # Set the working folder to the parent of the parent of this script
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Save the all-in-one mode
        os.environ['ALL_IN_ONE'] = str(all_in_one)
        
        # Invoke the export extractor
        if extracted_from_exports_run:
            extracted_from_exports()
        
        # Invoke the contents packer
        if contents_from_extracted_run:
            contents_from_extracted()
        
        # Invoke the cpk packer
        if patches_from_contents_run:
            patches_from_contents()
    

if __name__ == "__main__":
    run_type = None

    intro_print()

    run_type = sys.argv[1]

    if run_type is None:
        run_type_request()

    main(run_type)