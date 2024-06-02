import os
import sys
import ctypes

from .pausing import pause
from .FILE_INFO import ADMIN_WARNED_PATH


def admin_check(folder_location):
    """
    Collection of system folders on which PES is usually installed
    These folders need admin rights for copying cpks into them

    Other folder names included in this check (they contain "Program"):
    "Programmes", "Programme", "Programfájlok", "Programmi", "Programmer",
    "Program", "Program Dosyaları", "Programfiler", "Programas"

    If you have pes installed in a system folder not included in this check
    please let me know and set admin_mode to 1 in the settings in the meanwhile
    """
    for folder in ["Program", "Archivos", "Arquivos", "Pliki", "Fisiere"]:
        if folder_location[3:].lower().startswith(folder.lower()):
            return 1
    return 0


def admin_request(run_path, run_type):

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

        if not os.path.exists(ADMIN_WARNED_PATH):
            print('Either accept the incoming request or disable Move Cpks mode in the settings file.')
            print('-')

            pause()

            with open(ADMIN_WARNED_PATH, 'w') as f:
                f.write('This file tells the program that you know why the request for admin privileges is needed.')

        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", run_path, run_type, None, 1)

        # Exit the program
        sys.exit()
