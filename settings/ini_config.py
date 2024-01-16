"""Load configuration from .ini file."""
import configparser
import os

env = os.getenv("ENVTYPE", "test")
# Read local file `settings.ini`.
if env == "test":
    config = configparser.ConfigParser()
    config.read('settings/test.ini')
else:
    config = configparser.ConfigParser()
    config.read('prod.ini')







