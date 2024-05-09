import os

from python.lib.utils import logging_tools


def log_username_clean(log_name):

    if not os.path.exists(log_name):
        return

    username = os.getenv("USERNAME", "unknown")

    with open(log_name, "r") as f:
        text = f.readlines()

    text = [line.replace(f"\\{username}\\", "\\<username>\\") for line in text]

    with open(log_name, "w") as f:
        f.writelines(text)


if __name__ == "__main__":

    log_username_clean(logging_tools.ISSUES_LOG_NAME)
    log_username_clean(logging_tools.CRASH_LOG_NAME)
