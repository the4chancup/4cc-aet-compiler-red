import os
import logging

from . import COLORS
from .pausing import pause


SUGGESTIONS_LOG_NAME = "suggestions.log"
ISSUES_LOG_NAME = "issues.log"
CRASH_LOG_NAME = "crash.log"


class ColorFilter(logging.Filter):
    """
    This is a filter which colorizes the alert words "FATAL", "ERROR" and "Warning".
    """

    def filter(self, record):

        FATAL_STRING = "FATAL"
        FATAL_STRING_COLORED = COLORS.DARK_RED + "FATAL" + COLORS.RESET
        record.msg = record.msg.replace(FATAL_STRING, FATAL_STRING_COLORED)

        ERROR_STRING = "ERROR"
        ERROR_STRING_COLORED = COLORS.DARK_RED + "ERROR" + COLORS.RESET
        record.msg = record.msg.replace(ERROR_STRING, ERROR_STRING_COLORED)

        WARNING_STRING = "Warning"
        WARNING_STRING_COLORED = COLORS.DARK_YELLOW + "Warning" + COLORS.RESET
        record.msg = record.msg.replace(WARNING_STRING, WARNING_STRING_COLORED)

        return True


def log_store(log_name):

    if not os.path.exists(log_name):
        return

    log_name_old = log_name + ".old"

    if os.path.exists(log_name_old):
        os.remove(log_name_old)

    try:
        os.rename(log_name, log_name_old)
    except OSError:
        print(f"- An error occurred while trying to rename the {log_name} file")
        print( "- Please check if it's open in another program")
        print( "-")
        pause("Press any key to continue after checking... ")
        os.rename(log_name, log_name_old)


def logger_init(__name__):

    # Set the root logger level
    logging.getLogger().setLevel(logging.INFO)


    # If a suggestions log file already exists, add .old to it
    log_store(SUGGESTIONS_LOG_NAME)

    # Create a file handler which will only store INFO messages
    # It will only create a file when a message occurs
    suggestions_log_handler = logging.FileHandler(SUGGESTIONS_LOG_NAME, delay=True)
    suggestions_log_handler.setLevel(logging.INFO)
    suggestions_log_handler.addFilter(lambda record: record.levelno == logging.INFO)

    # Add it to the root logger
    logging.getLogger().addHandler(suggestions_log_handler)


    # If an issues log file already exists, add .old to it
    log_store(ISSUES_LOG_NAME)

    # Create a file handler which which will only store WARNING messages or higher
    # It will only create a file when a message occurs
    issues_log_handler = logging.FileHandler(ISSUES_LOG_NAME, delay=True)
    issues_log_handler.setLevel(logging.WARNING)

    # Add it to the root logger
    logging.getLogger().addHandler(issues_log_handler)


    # Create a stream handler for outputting colored errors to stderr
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.ERROR)
    stream_handler.addFilter(ColorFilter())

    # Add it to the root logger
    logging.getLogger().addHandler(stream_handler)


    # If a crash log file already exists, add .old to it
    log_store(CRASH_LOG_NAME)

    # Create a logger
    logger = logging.getLogger(__name__)

    # Create a file handler which will only create a file when an exception occurs
    crash_log_handler = logging.FileHandler(CRASH_LOG_NAME, delay=True)

    # Create a formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)-15s - %(name)s - %(levelname)s - %(message)s')
    crash_log_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(crash_log_handler)

    return logger
