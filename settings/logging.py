from pydantic.v1 import BaseSettings
import os

from ait_openapi.bella_trace import TraceContext

from doc_parser.context import logger_context

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
    if not os.path.exists("/data0/www/applogs"):
        os.makedirs("/data0/www/applogs", exist_ok=True)
    file_handler = TimedRotatingFileHandler(filename="/data0/www/applogs/app.log", when="D", interval=1, backupCount=14)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger

def _setup_logger():
    document_parser_logger = init_logger()
    # 注册日志记录器
    logger_context.register_logger(document_parser_logger)

_setup_logger()
