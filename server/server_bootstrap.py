
# 服务最先启动模块，在容器启动之前，用于初始化一些信息
from doc_parser.context import logger_context
from settings import settings_path
from settings.ini_config import init_config
from settings.logging import init_logger

init_config(settings_path)
# 初始化日志配置
def _setup_logger():
    document_parser_logger = init_logger()
    # 注册日志记录器
    logger_context.register_logger(document_parser_logger)

_setup_logger()