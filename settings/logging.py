"""Logging configuration for Bella-Api."""
import datetime
import logging
import os
from logging.handlers import TimedRotatingFileHandler

from bella_openapi.bella_trace import TraceContext

from settings.ini_config import config

_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class TraceContextFilter(logging.Filter):
    """添加trace_id到日志记录中"""
    def filter(self, record):
        record.trace_id = TraceContext.trace_id
        return True

class UTC8TimeFormatter(logging.Formatter):
    """A logging formatter that adjusts times to UTC+8."""
    def formatTime(self, record, datefmt=None):
        # 将记录的创建时间调整为UTC+8
        ct = self.converter(record.created + 8*3600)
        if datefmt:
            s = datetime.datetime.fromtimestamp(record.created).strftime(datefmt)[:-3]  # 只保留3位毫秒
        else:
            try:
                s = datetime.datetime.fromtimestamp(record.created).strftime(self.default_time_format)[:-3]
            except ValueError:
                s = datetime.datetime.fromtimestamp(record.created).strftime(self.default_time_format[:-2] + self.default_msec_format)[:-3]
                s = s.replace('+0000', '')
        return s

class NewLineFormatter(logging.Formatter):
    """Adds logging prefix to newlines to align multi-line messages."""

    def __init__(self, fmt, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        msg = super().format(record)
        if record.message != "":
            parts = msg.split(record.message)
            msg = msg.replace("\n", "\r\n" + parts[0])
        return msg


def init_logger():
    logger = logging.getLogger('document_parser')
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    formatter = UTC8TimeFormatter('[%(trace_id)s] -%(asctime)s - %(module)s - %(levelname)s - %(message)s', _DATE_FORMAT)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    # 添加trace_id过滤器
    logger.addFilter(TraceContextFilter())
    #配置日志文件滚动
    log_dir = str(config.get("LOG", "dir"))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, str(config.get("LOG", "log_file")))
    file_handler = TimedRotatingFileHandler(filename=log_file_path, when="D", interval=1, backupCount=14)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


