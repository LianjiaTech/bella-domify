"""Load configuration from .ini file."""
import configparser
import os
import logging

env = os.getenv("ENVTYPE", "test")
# Read local file `settings.ini`.
config = configparser.ConfigParser()
if env == "test":
    config.read(os.path.join(os.path.dirname(__file__), "test.ini"))
else:
    config.read(os.path.join(os.path.dirname(__file__), "prod.ini"))


if "S3" not in config:
    logging.error(rf'config读取失败, config: {config}')
    raise Exception("config读取失败")
