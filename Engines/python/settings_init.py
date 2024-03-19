import os
import configparser

def settings_init(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)

    for section in config.sections():
        for key, value in config.items(section):
            os.environ[key] = value
