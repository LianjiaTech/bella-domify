# fastapi定义接口
import logging
from threading import Thread

import uvicorn

from server import layout_parse
from .task_executor.task_manager import create_pdf_parse_task
from .task_executor.executor import execute_parse_task

from fastapi import FastAPI, Form, Path, Body
from fastapi import File, UploadFile

from pdf2docx import Converter
from pdf2docx.dom_tree.domtree import DomTreeModel
from server.log.log_config import log_config

log_config()  # 初始化日志配置

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/actuator/health/liveness")
async def health_liveness():
    return {"status": "UP"}


@app.get("/actuator/health/readiness")
async def health_readiness():
    return {"status": "UP"}


# 上传文件接口
@app.post("/pdf/parse/test")
async def create_upload_file(file: UploadFile = File(...)):
    # 读取file字节流
    contents = await file.read()
    converter = Converter(stream=contents)
    dom_tree = converter.dom_tree_parse(
        remove_watermark=True,
        parse_stream_table=False
    )
    return DomTreeModel(dom_tree=dom_tree)


# 文件解析-获取版面信息
@app.post("/parse/getLayoutData")
async def create_upload_file(file_name: str = Form(...), file_url_object: UploadFile = File(...)):
    # 读取file字节流
    contents = await file_url_object.read()
    return layout_parse.layout_data_parse(file_name, contents)


@app.post("/async/pdf/parse")
async def async_parse(file: UploadFile = File(...), callback_url: str = Form(...)):
    # 读取file字节流
    return create_pdf_parse_task(file, callback_url)


# 定义回调接口，url中包含pathvariable
@app.post("/async/pdf/parse/callback/{taskNo}")
async def async_parse_callback(taskNo: str = Path(..., title="The task number"), task: dict = Body(...)):
    logging.info("接收回调")
    print(taskNo, task)


@app.on_event("startup")
async def startup_event():
    print("Starting background task...")
    thread = Thread(target=execute_parse_task)
    thread.start()


# if __name__ == "__main__":
#     uvicorn.run("server.api:app", host="127.0.0.1", port=8080, reload=True)
