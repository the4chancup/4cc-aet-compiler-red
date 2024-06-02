import os

from python.lib.utils.FILE_INFO import (
    ISSUES_LOG_PATH,
    CRASH_LOG_PATH
)


def log_username_clean(log_path):

    if not os.path.exists(log_path):
        return

    username = os.getenv("USERNAME", "unknown")

    with open(log_path, "r") as f:
        text = f.readlines()

    text = [line.replace(f"\\{username}\\", "\\<username>\\") for line in text]

    with open(log_path, "w") as f:
        f.writelines(text)


if __name__ == "__main__":

    log_username_clean(ISSUES_LOG_PATH)
    log_username_clean(CRASH_LOG_PATH)
