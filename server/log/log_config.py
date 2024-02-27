import logging
import sys
from loguru import logger

from settings.logging import log_settings


def log_config():
    level = log_settings.LOG_LEVEL
    path = log_settings.LOG_PATH
    retention = log_settings.LOG_RETENTION

    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(level)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # configure loguru
    logger.configure(
        handlers=[
            {"sink": sys.stdout},
            {"sink": path, "rotation": "00:00", "retention": retention},
            {"sink": log_settings.FIX_LOG_PATH, "rotation": "500 MB", "retention": retention},
        ]
    )


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


