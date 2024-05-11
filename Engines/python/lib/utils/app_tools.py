import os
import sys

from python.lib.utils import APP_DATA


def intro_print():
    if sys.platform == "win32":
        os.system("color")
    version_string = f'{APP_DATA.VERSION_MAJOR}.{APP_DATA.VERSION_MINOR}.{APP_DATA.VERSION_PATCH}'
    dev_string = "-\033[96mdev\033[0m" if APP_DATA.VERSION_DEV else ""
    print('-')
    print('-')
    print('- 4cc aet compiler ' + '\033[91m' + 'Red' + '\033[0m' + f' {version_string}' + f'{dev_string}')
    print('-')
    print('-')
