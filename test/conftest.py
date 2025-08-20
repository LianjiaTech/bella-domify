from doc_parser.context import ParserConfig, parser_context
from doc_parser.dom_parser.provider.image_provider import ImageStorageProvider
from services.provider.openai_vision_model_provider import OpenAIVisionModelProvider
from settings import settings_path
from settings.ini_config import config, init_config


class EmptyImageStorageProvider(ImageStorageProvider):
    """
    一个空的图片存储提供者，用于测试时不需要实际存储图片。
    """

    def upload(self, image: bytes) -> str:
        return ""

    def download(self, file_key: str) -> bytes:
        return b""


def pytest_sessionstart(session):
    init_config(settings_path)
    parser_config = ParserConfig(image_provider=EmptyImageStorageProvider(),
                                 ocr_model_name=config.get('OCR', 'model_name'),
                                 ocr_enable=config.getboolean('OCR', 'enable'),
                                 user="0000000000000001",
                                 vision_model_provider=OpenAIVisionModelProvider())
    parser_context.register_all_config(parser_config)


def pytest_sessionfinish(session):
    print("pytest_sessionfinish - 测试结束后")
