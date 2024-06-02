import os


from . import COLORS
from .APP_DATA import (
    APP_VERSION_MAJOR,
    APP_VERSION_MINOR,
    APP_VERSION_PATCH,
    APP_VERSION_DEV,
)
from .FILE_INFO import (
    SUGGESTIONS_LOG_PATH,
    ISSUES_LOG_PATH,
)



def app_title(colorize=True):

    color_bright_cyan = COLORS.BRIGHT_CYAN if colorize else ""
    color_bright_red = COLORS.BRIGHT_RED if colorize else ""
    color_reset = COLORS.RESET if colorize else ""

    version_string = f"{APP_VERSION_MAJOR}.{APP_VERSION_MINOR}.{APP_VERSION_PATCH}"
    dev_string = f"-{color_bright_cyan}dev{color_reset}" if APP_VERSION_DEV else ""

    title_string = f"4cc aet compiler {color_bright_red}Red{color_reset} {version_string}{dev_string}"

    return title_string


def log_presence_warn():
    if os.path.exists(ISSUES_LOG_PATH):
        # Warn about there being some issues and about having to open the log
        print( "-")
        print(f"- {COLORS.DARK_YELLOW}Warning{COLORS.RESET}: There were some potential issues in the exports")
        print( "- Please check the issues.log file for more details")
    else:
        print( "-")
        print(f"- {COLORS.DARK_GREEN}No issues were found{COLORS.RESET}")

    if os.path.exists(SUGGESTIONS_LOG_PATH):
        # Warn about there being some suggestions
        print( "-")
        print(f"- {COLORS.DARK_CYAN}Info{COLORS.RESET}: There are some suggestions available")
        print( "- Check the suggestions.log file to improve your aesthetics")
