# web容器启动前的初始化操作，不要删除这个导入
from . import server_bootstrap

import json
import time
from threading import Thread

from fastapi import FastAPI

from doc_parser.context import parser_context, ParserConfig, logger_context
from services.constants import GROUP_ID_LONG_TASK, GROUP_ID_IMAGE_TASK, GROUP_ID_SHORT_TASK
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
    global background_threads
    print("Starting background task...")

    # 启动子进程，GROUP_ID_LONG_TASK 处理大文件
    thread1 = Thread(target=listen_parse_task_layout_and_domtree, args=(GROUP_ID_LONG_TASK,))
    thread1.start()

    # 启动子进程，GROUP_ID_SHORT_TASK 处理小文件
    thread2 = Thread(target=listen_parse_task_layout_and_domtree, args=(GROUP_ID_SHORT_TASK,))
    thread2.start()

    # 启动子进程，GROUP_ID_IMAGE_TASK 处理图片文件
    thread3 = Thread(target=listen_parse_task_layout_and_domtree, args=(GROUP_ID_IMAGE_TASK,))
    thread3.start()

    # 保存线程引用
    background_threads.extend([thread1, thread2, thread3])
    logging.info(f"已启动 {len(background_threads)} 个后台线程")
    monitor_thread = Thread(target=monitor_threads, daemon=True)
    monitor_thread.start()


def monitor_threads():
    global background_threads
    while True:
        for i, thread in enumerate(background_threads):
            if not thread.is_alive():
                logging.info(f"线程 {i} 已死亡，正在重启...")
                # 重新创建并启动相应的线程
                if i == 0:
                    new_thread = Thread(target=listen_parse_task_layout_and_domtree, args=(GROUP_ID_LONG_TASK,),
                                        daemon=True)
                elif i == 1:
                    new_thread = Thread(target=listen_parse_task_layout_and_domtree, args=(GROUP_ID_SHORT_TASK,),
                                        daemon=True)
                else:
                    new_thread = Thread(target=listen_parse_task_layout_and_domtree, args=(GROUP_ID_IMAGE_TASK,),
                                        daemon=True)
                new_thread.start()
                background_threads[i] = new_thread
        time.sleep(60)


@app.on_event("startup")
async def startup_event():
    print("Application startup")


@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown")
