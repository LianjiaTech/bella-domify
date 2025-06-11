# 服务最先启动模块，在容器启动之前，用于初始化一些信息
from doc_parser.context import logger_context
from settings.logging import init_logger


# 初始化日志配置
def _setup_logger():
    document_parser_logger = init_logger()
    # 注册日志记录器
    logger_context.register_logger(document_parser_logger)

_setup_logger()