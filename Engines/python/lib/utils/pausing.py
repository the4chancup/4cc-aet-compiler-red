import os
import sys


def pause(message="Press any key to continue... "):
    """
    Pauses the program and waits for Enter.

    Args:
        message (str, optional): The message to be displayed before waiting for the user to press a key. Defaults to "Press any key to continue... ".

    Returns:
        None
    """

    print(message, end='', flush=True)

    if sys.platform == 'win32':
        os.system('pause >nul')
        print("")

    else:
        os.system("read -n1 -r")
