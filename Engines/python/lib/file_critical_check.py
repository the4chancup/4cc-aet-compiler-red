import os
import logging


def file_critical_check(file_path):
    if not os.path.isfile(file_path):
        logging.critical( "-")
        logging.critical(f"- FATAL ERROR - Missing \"{file_path}\" file")
        logging.critical( "-")
        logging.critical( "- Please grab it from the compiler's original 7z package")
        logging.critical( "-")
        logging.critical( "- The program will now close")
        print("-")
        input("Press Enter to continue...")

        exit()