import os

from .lib.utils.FILE_INFO import (
    ISSUES_LOG_PATH,
    CRASH_LOG_PATH
)


def username_clean_from_log(log_path):

    if not os.path.exists(log_path):
        return

    username = os.getenv("USERNAME", "unknown")

    with open(log_path, "r", encoding='utf-8') as f:
        text = f.readlines()

    text = [line.replace(f"\\{username}\\", "\\<username>\\") for line in text]

    with open(log_path, "w", encoding='utf-8') as f:
        f.writelines(text)

def username_clean_from_logs():
    username_clean_from_log(ISSUES_LOG_PATH)
    username_clean_from_log(CRASH_LOG_PATH)


if __name__ == "__main__":

    username_clean_from_logs()
