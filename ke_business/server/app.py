# web容器启动前的初始化操作，不要删除这个导入
from . import server_bootstrap
from services.provider.s3_image_provider import S3ImageStorageProvider

from services.provider.openai_vision_model_provider import OpenAIVisionModelProvider
from fastapi import FastAPI

from doc_parser.context import parser_context, ParserConfig, logger_context
from settings.ini_config import config

from server.api import router, health_router
from server.workers import start_workers, stop_workers

logger = logger_context.get_logger()
app = FastAPI()

app.include_router(router)
app.include_router(health_router)

background_threads = []


# 文件解析 - 监听解析任务，异步解析
@app.on_event("startup")
async def startup_event():
    parser_config = ParserConfig(image_provider=S3ImageStorageProvider(),
                                 ocr_model_name=config.get('OCR', 'model_name'),
                                 ocr_enable=config.getboolean('OCR', 'enable'),
                                 vision_model_provider=OpenAIVisionModelProvider())

    parser_context.register_all_config(parser_config)

    logger.info('Starting Kafka consumer thread...')
    start_workers()
    logger.info('Starting Kafka consumer thread ok...')


@app.on_event("shutdown")
async def shutdown_event():
    # 使用导入的logger，不需要重新获取
    logger.info('Stopping Kafka consumer thread...')
    stop_workers()
    logger.info('Stopping Kafka consumer thread ok...')
    logger.info("Application shutdown")
