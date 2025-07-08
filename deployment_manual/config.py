import configparser
import os

def get_config():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
    return config

def get(section, option, default=None):
    try:
        return get_config().get(section, option)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default
