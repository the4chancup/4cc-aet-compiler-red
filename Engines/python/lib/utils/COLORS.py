import os
import sys


if sys.platform == "win32":

    # Enable color on Windows 10+ only
    win_version = sys.getwindowsversion().major

    # Check if the NO_COLOR environment variable is set
    colorize = "NO_COLOR" not in os.environ and win_version >= 10

    if colorize:
        os.system("color")

else:
    # Check if the NO_COLOR environment variable is set
    colorize = "NO_COLOR" not in os.environ

BLACK          = '\033[30m' if colorize else ''

DARK_RED       = '\033[31m' if colorize else ''
DARK_GREEN     = '\033[32m' if colorize else ''
DARK_YELLOW    = '\033[33m' if colorize else ''
DARK_BLUE      = '\033[34m' if colorize else ''
DARK_MAGENTA   = '\033[35m' if colorize else ''
DARK_CYAN      = '\033[36m' if colorize else ''
DARK_WHITE     = '\033[37m' if colorize else ''

BRIGHT_BLACK   = '\033[90m' if colorize else ''
BRIGHT_RED     = '\033[91m' if colorize else ''
BRIGHT_GREEN   = '\033[92m' if colorize else ''
BRIGHT_YELLOW  = '\033[93m' if colorize else ''
BRIGHT_BLUE    = '\033[94m' if colorize else ''
BRIGHT_MAGENTA = '\033[95m' if colorize else ''
BRIGHT_CYAN    = '\033[96m' if colorize else ''
WHITE          = '\033[97m' if colorize else ''

RESET          = '\033[0m' if colorize else ''
