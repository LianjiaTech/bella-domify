# web容器启动前的初始化操作，不要删除这个导入
from . import server_bootstrap
from services.provider.s3_parse_result_cache_provider import S3ParseResultCacheProvider
from fastapi import FastAPI

from doc_parser.context import parser_context, ParserConfig, logger_context
from services.provider.openai_vision_model_provider import OpenAIVisionModelProvider
from services.provider.s3_image_provider import S3ImageStorageProvider
from settings.ini_config import config
from .api import router, health_router
from .task_executor.executor import listen_parse_task_layout_and_domtree

logger = logger_context.get_logger()
app = FastAPI()

app.include_router(router)
app.include_router(health_router)

background_threads = []


# 文件解析 - 监听解析任务，异步解析
@app.on_event("startup")
async def startup_event():
    import os
    
    parser_config = ParserConfig(image_provider=S3ImageStorageProvider(),
                                 parse_result_cache_provider=S3ParseResultCacheProvider(),
                                 ocr_model_name=config.get('OCR', 'model_name'),
                                 ocr_enable=config.getboolean('OCR', 'enable'),
                                 vision_model_provider=OpenAIVisionModelProvider())

    # 启动子进程，GROUP_ID_LONG_TASK 处理大文件
    thread1 = Thread(target=listen_parse_task_layout_and_domtree, args=(GROUP_ID_LONG_TASK,))
    thread1.start()

    # 只有主worker进程启动Kafka消费者，避免重复消费
    worker_id = os.getenv('UVICORN_WORKER_ID', '0')
    if worker_id == '0':
        logger.info('Starting Kafka consumer thread...')
        start_workers()
        logger.info('Starting Kafka consumer thread ok...')
    else:
        logger.info(f'Worker {worker_id} skipping Kafka consumer startup')


@app.on_event("shutdown")
async def shutdown_event():
    import os
    
    # 只有启动了Kafka消费者的worker才需要停止
    worker_id = os.getenv('UVICORN_WORKER_ID', '0')
    if worker_id == '0':
        # 使用导入的logger，不需要重新获取
        logger.info('Stopping Kafka consumer thread...')
        stop_workers()
        logger.info('Stopping Kafka consumer thread ok...')
    logger.info("Application shutdown")
