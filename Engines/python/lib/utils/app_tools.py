from python.lib.utils import APP_DATA


def app_title():

    version_string = f"{APP_DATA.VERSION_MAJOR}.{APP_DATA.VERSION_MINOR}.{APP_DATA.VERSION_PATCH}"
    dev_string = "-\033[96mdev\033[0m" if APP_DATA.VERSION_DEV else ""

    title_string = f"- 4cc aet compiler \033[91mRed\033[0m {version_string}{dev_string}"

    return title_string
