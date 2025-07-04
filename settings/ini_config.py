"""Load configuration from .ini file."""
import configparser
import os

from utils.tokens_util import init_tiktoken

config = configparser.ConfigParser()

def init_config(base_dir):
    env = os.getenv("ENVTYPE", "test")
    # Read local file `settings.ini`.
    if env == "test":
        config.read(os.path.join(base_dir, "test.ini"))
    else:
        config.read(os.path.join(base_dir, "prod.ini"))

init_tiktoken()