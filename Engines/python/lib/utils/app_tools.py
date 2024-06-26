from . import APP_DATA
from . import COLORS


def app_title(colorize=True):

    color_bright_cyan = COLORS.BRIGHT_CYAN if colorize else ""
    color_bright_red = COLORS.BRIGHT_RED if colorize else ""
    color_reset = COLORS.RESET if colorize else ""

    version_string = f"{APP_DATA.VERSION_MAJOR}.{APP_DATA.VERSION_MINOR}.{APP_DATA.VERSION_PATCH}"
    dev_string = f"-{color_bright_cyan}dev{color_reset}" if APP_DATA.VERSION_DEV else ""

    title_string = f"4cc aet compiler {color_bright_red}Red{color_reset} {version_string}{dev_string}"

    return title_string
