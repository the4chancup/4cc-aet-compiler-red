import os
import sys
from .app_tools import app_title


def pause(message="Press any key to continue... ", print_hyphen=True, force=False):
    """
    Pauses the program and waits for Enter.

    Args:
        message (str, optional): The message to be displayed before waiting for the user to press a key. Defaults to "Press any key to continue... ".

    Returns:
        None
    """
    pause_allow = os.environ.get('PAUSE_ALLOW', '1')
    if pause_allow == '0' and not force:
        return

    if print_hyphen:
        print("-")

    print(message, end='', flush=True)

    if sys.platform == 'win32':
        if print_hyphen:
            # Set the console title
            os.system("title " + "Paused - " + app_title(colorize=False))
            # Flash the console window
            import ctypes
            ctypes.windll.user32.FlashWindow(ctypes.windll.kernel32.GetConsoleWindow(), True)

        os.system('pause >nul')

        if print_hyphen:
            # Set the console title
            os.system("title " + "_ - " + app_title(colorize=False))

        print("")

    else:
        os.system("read -n1 -r")
