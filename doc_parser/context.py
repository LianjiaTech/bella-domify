from logging import Logger
from typing import Optional, Callable
import contextvars


from pydantic import BaseModel, ConfigDict

from doc_parser.dom_parser.provider.image_provider import ImageStorageProvider
from doc_parser.dom_parser.provider.parse_result_cache_provider import ParseResultCacheProvider
from doc_parser.dom_parser.provider.vision_model_provider import VisionModelProvider


class ParserConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # 图像存储必填
    image_provider: ImageStorageProvider
    # ocr相关
    vision_model_list: Optional[list[str]] = None
    vision_model_provider: Optional[VisionModelProvider] = None
    parse_result_cache_provider: Optional[ParseResultCacheProvider] = None
    ocr_model_name:Optional[str] = None
    ocr_enable: bool = False
    user: Optional[str] = None  # 用户标识，用于上下文传递

def run_with_context_in_thread(func: Callable):
    """
    在线程中运行函数前，传递当前线程的用户信息

    用法:
    Args:
        func: 要执行的函数
    Returns:
        一个可调用对象，在被调用时会设置正确的用户上下文并执行原函数
    """
    # 获取当前线程的用户信息
    current_user = parser_context.get_user()

    # 定义一个包装函数，在执行时设置用户信息
    def wrapper(*args, **kwargs):
        # 设置用户信息
        parser_context.register_user(current_user)
        # 执行原函数
        return func(*args, **kwargs)

    # 返回包装函数
    return wrapper


class ParserContext:
    # 创建全局的 ContextVar 对象来存储用户信息，线程安全，明确指定类型为 Optional[str]
    _user_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('user', default=None)

    def __init__(self, config: [ParserConfig, dict] = None):
        self._register_all_config(config)

    def register_all(self, parser_context: 'ParserContext'):
        """
        初始化解析上下文。
        Args:
            parser_context (ParserContext): 另一个 ParserContext 实例，用于复制配置。
        """
        self.image_provider = parser_context.image_provider
        self.vision_model_list = parser_context.vision_model_list
        self.ocr_model_name = parser_context.ocr_model_name
        self.ocr_enable = parser_context.ocr_enable
        self.vision_model_provider = parser_context.vision_model_provider
        self.parse_result_cache_provider = parser_context.parse_result_cache_provider

    def register_all_config(self, config: Optional[ParserConfig] = None):
        self._register_all_config(config)

    def _register_all_config(self, config: Optional[ParserConfig] = None):
        """
          初始化解析上下文。
          Args:
              config (dict): 解析配置参数。
        """
        if config:
            self.image_provider = config.image_provider
            self.vision_model_list = config.vision_model_list
            self.ocr_model_name = config.ocr_model_name
            self.ocr_enable = config.ocr_enable
            self.vision_model_provider = config.vision_model_provider
            self.parse_result_cache_provider = config.parse_result_cache_provider
            self.register_user(config.user)

    def register_image_provider(self, image_provider: ImageStorageProvider):
        self.image_provider = image_provider

    """
    使用全局 ContextVar 的 LLM 上下文类，用于存储用户信息，支持异步编程
    """
    def register_user(self, user: str):
        """
        设置用户信息
        Args:
            user: 用户标识
        """
        self._user_var.set(user)

    def get_user(self) -> Optional[str]:
        """
        获取用户信息
        Returns:
            用户标识
        """
        return self._user_var.get()

    def register_vision_model_list(self, model_list: list[str]):
        self.vision_model_list = model_list

    def register_vision_model_provider(self, vision_model_provider: VisionModelProvider):
            self.vision_model_provider = vision_model_provider

    def register_parse_result_cache_provider(self, parse_result_cache_provider: ParseResultCacheProvider):
        self.parse_result_cache_provider = parse_result_cache_provider


# 创建应用上下文
parser_context = ParserContext()


class LoggerContext:

    def __init__(self):
        self.logger = Logger.root  # 默认使用根日志记录器

    def register_logger(self, logger):
        """
        注册日志记录器。
        Args:
            logger: 日志记录器实例。
        """
        self.logger = logger


    def get_logger(self):
        """
        记录日志消息。
        Args:
            name (str): a logger with the specified name, creating it if necessary.If no name is specified, return the root logger.
        """
        return self.logger

# 创建日志上下文
logger_context = LoggerContext()