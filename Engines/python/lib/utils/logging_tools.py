import os
import logging


ISSUES_LOG_NAME = "issues.log"
ERROR_LOG_NAME = "error.log"


class ColorFilter(logging.Filter):
    """
    This is a filter which colorizes some alert words.

    - "FATAL" gets turned into "\033[31mFATAL\033[0m" (red text)
    - "ERROR" gets turned into "\033[31mERROR\033[0m" (red text)
    - "Warning" gets turned into "\033[33mWarning\033[0m" (yellow text)
    """

    def filter(self, record):

        FATAL_STRING = "FATAL"
        FATAL_STRING_COLORED = "\033[31mFATAL\033[0m"
        record.msg = record.msg.replace(FATAL_STRING, FATAL_STRING_COLORED)

        ERROR_STRING = "ERROR"
        ERROR_STRING_COLORED = "\033[31mERROR\033[0m"
        record.msg = record.msg.replace(ERROR_STRING, ERROR_STRING_COLORED)

        WARNING_STRING = "Warning"
        WARNING_STRING_COLORED = "\033[33mWarning\033[0m"
        record.msg = record.msg.replace(WARNING_STRING, WARNING_STRING_COLORED)

        return True


def log_store(log_name):
    if os.path.exists(log_name):
        log_name_old = log_name + ".old"
        if os.path.exists(log_name_old):
            os.remove(log_name_old)
        try:
            os.rename(log_name, log_name_old)
        except OSError:
            print(f"- An error occurred while trying to rename the {log_name} file")
            print("- Please check if it's open in another program")
            print("-")
            input("Press Enter to continue after checking...")
            os.rename(log_name, log_name_old)


def logger_init(__name__):

    # If an issues log file already exists, add .old to it
    log_store(ISSUES_LOG_NAME)

    # Create a file handler which will only create a file when a WARNING or higher occurs
    file_handler = logging.FileHandler(ISSUES_LOG_NAME, delay=True)
    file_handler.setLevel(logging.WARNING)

    # Add it to the root logger
    logging.getLogger().addHandler(file_handler)

    # Create a stream handler for outputting colored errors to stderr
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.ERROR)
    stream_handler.addFilter(ColorFilter())

    # Add it to the root logger
    logging.getLogger().addHandler(stream_handler)


    # If an error log file already exists, add .old to it
    log_store(ERROR_LOG_NAME)

    # Create a logger
    logger = logging.getLogger(__name__)

    # Create a file handler which will only create a file when an exception occurs
    handler = logging.FileHandler(ERROR_LOG_NAME, delay=True)

    # Create a formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)-15s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger
