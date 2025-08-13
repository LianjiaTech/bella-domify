from pydantic.v1 import BaseSettings
import os

from ait_openapi.bella_trace import TraceContext

from settings.ini_config import config

_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LOG_PATH: str = base_path + "/app-{time:YYYY-MM-DD}.log"
    FIX_LOG_PATH: str = base_path + "/app.log"
    LOG_RETENTION: str = "14 days"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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


