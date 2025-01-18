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


def referee_title(colorize=True):

    color_dark_magenta = COLORS.DARK_MAGENTA if colorize else ""
    color_reset = COLORS.RESET if colorize else ""

    title_string = f"{color_dark_magenta}referees{color_reset} "

    return title_string


def pes_title(pes_version, colorize=True):

    color_bright_red = COLORS.BRIGHT_RED if colorize else ""
    color_bright_green = COLORS.BRIGHT_GREEN if colorize else ""
    color_bright_yellow = COLORS.BRIGHT_YELLOW if colorize else ""
    color_bright_blue = COLORS.BRIGHT_BLUE if colorize else ""
    color_bright_magenta = COLORS.BRIGHT_MAGENTA if colorize else ""
    color_bright_cyan = COLORS.BRIGHT_CYAN if colorize else ""
    color_reset = COLORS.RESET if colorize else ""

    match pes_version:
        case 16:
            pes_color = color_bright_magenta
        case 17:
            pes_color = color_bright_yellow
        case 18:
            pes_color = color_bright_cyan
        case 19:
            pes_color = color_bright_blue
        case 21:
            pes_color = color_bright_green
        case _:
            pes_color = color_bright_red

    title_string = f"{pes_color}PES20{pes_version}{color_reset}"

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
