# fastapi定义接口
import logging
from threading import Thread

from fastapi import FastAPI, APIRouter
from fastapi import File, UploadFile
from fastapi import Form, Path, Body

from server.log.log_config import log_config
from services import layout_parse, domtree_parse
from .context import user_context
from .task_executor.executor import execute_parse_task
from .task_executor.task_manager import create_pdf_parse_task

# TODO 兼容阶段，业务方添加 user 之后下掉
DEFAULT_USER = "1000000020353701"

log_config()  # 初始化日志配置

app = FastAPI()

router = APIRouter(prefix="/v1/parser")


@router.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/actuator/health/liveness")
async def health_liveness():
    return {"status": "UP"}


@app.get("/actuator/health/readiness")
async def health_readiness():
    return {"status": "UP"}


# 上传文件接口
@router.post("/pdf/parse/test")
async def create_upload_file(file: UploadFile = File(...), user: str = Form(default=None)):
    user_context.set(user or DEFAULT_USER)
    # 读取file字节流
    contents = await file.read()
    return domtree_parse.parse(contents)


# 文件解析-获取版面信息
@router.post("/document/layout/parse")
async def create_upload_file(file_name: str = Form(...), file_url_object: UploadFile = File(...), 
                             user: str = Form(default=None)):
    user_context.set(user or DEFAULT_USER)
    # 读取file字节流
    contents = await file_url_object.read()
    return layout_parse.parse(file_name, contents)


@router.post("/async/pdf/parse")
async def async_parse(file: UploadFile = File(...), callback_url: str = Form(...), user: str = Form(default=None)):
    # 读取file字节流
    return create_pdf_parse_task(file, callback_url, user or DEFAULT_USER)


# 定义回调接口，url中包含pathvariable
@router.post("/async/pdf/parse/callback/{taskNo}")
async def async_parse_callback(taskNo: str = Path(..., title="The task number"), task: dict = Body(...)):
    logging.info("接收回调")
    print(taskNo, task)


@router.on_event("startup")
async def startup_event():
    print("Starting background task...")
    thread = Thread(target=execute_parse_task)
    thread.start()


## 历史path兼容，下个版本删除
router_without_prefix = APIRouter()


@router_without_prefix.get("/")
async def root():
    return {"message": "Hello World"}


@router_without_prefix.get("/actuator/health/liveness")
async def health_liveness():
    return {"status": "UP"}


@router_without_prefix.get("/actuator/health/readiness")
async def health_readiness():
    return {"status": "UP"}


# 上传文件接口
@router_without_prefix.post("/pdf/parse/test")
async def create_upload_file(file: UploadFile = File(...)):
    # 读取file字节流
    contents = await file.read()
    return domtree_parse.parse(contents)


# 文件解析-获取版面信息
@router_without_prefix.post("/document/layout/parse")
async def create_upload_file(file_name: str = Form(...), file_url_object: UploadFile = File(...)):
    # 读取file字节流
    contents = await file_url_object.read()
    return layout_parse.parse(file_name, contents)


@router_without_prefix.post("/async/pdf/parse")
async def async_parse(file: UploadFile = File(...), callback_url: str = Form(...)):
    # 读取file字节流
    return create_pdf_parse_task(file, callback_url)


# 定义回调接口，url中包含pathvariable
@router_without_prefix.post("/async/pdf/parse/callback/{taskNo}")
async def async_parse_callback(taskNo: str = Path(..., title="The task number"), task: dict = Body(...)):
    logging.info("接收回调")
    print(taskNo, task)


@router_without_prefix.on_event("startup")
async def startup_event():
    print("Starting background task...")
    thread = Thread(target=execute_parse_task)
    thread.start()


app.include_router(router)
app.include_router(router_without_prefix)


@app.on_event("startup")
async def startup_event():
    print("Application startup")


@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown")

# if __name__ == "__main__":
#     import uvicorn
#
#     uvicorn.run("server.api:app", host="127.0.0.1", port=8080, reload=True)
