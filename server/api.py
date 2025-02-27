# fastapi定义接口
import logging
from threading import Thread

from fastapi import FastAPI, APIRouter
from fastapi import File, UploadFile
from fastapi import Form, Path, Body, Query

from server.log.log_config import log_config
from services import parse_manager
from services.domtree_parser import pdf_parser
from .context import user_context, DEFAULT_USER
from .task_executor.executor import listen_parse_task_layout_and_domtree
from .task_executor.task_manager import create_pdf_parse_task

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


# 上传pdf文件接口，结构解析
@router.post("/pdf/parse/test")
async def create_upload_file(file: UploadFile = File(...), user: str = Form(default=None)):
    user_context.set(user or DEFAULT_USER)
    # 读取file字节流
    contents = await file.read()
    return pdf_parser.pdf_parse(contents)[0]


# 获取版面信息
@router.post("/document/layout/parse")
async def create_upload_file(file_name: str = Form(...), file_url_object: UploadFile = File(...), 
                             user: str = Form(default=None)):
    user_context.set(user or DEFAULT_USER)
    # 读取file字节流
    contents = await file_url_object.read()
    return parse_manager.layout_parse(file_name, contents)[0]   # todo luxu 临时保证老接口结构不变，后续修改


# 获取结构信息和字符串信息(直接串行解析)
@router.post("/document/parse")
async def document_parse(file_name: str = Form(...), file_url_object: UploadFile = File(...),
                         user: str = Form(default=None)):
    user_context.set(user or DEFAULT_USER)
    # 读取file字节流
    contents = await file_url_object.read()
    return parse_manager.parse_result_layout_and_domtree_sync(file_name, contents)


# 同步解析接口
@router.post("/document/parse/sync")
async def document_parse(file_id: str = Form(...), parse_type: str = Form(default="all"),
                         check_faq: bool = Form(default=True),
                         user: str = Form(default=None)):
    user_context.set(user or DEFAULT_USER)
    return parse_manager.parse_layout_and_domtree_sync_by_file_id(file_id, parse_type, check_faq)


# 获取S3缓存结果: 通过file_id获取解析结果（结构信息和字符串信息）
@router.get("/document/parse/{file_id}")
async def document_parse(file_id: str = Path(...), parse_type: str = Query(default="all")):
    return parse_manager.api_get_result_service(file_id, parse_type)


@router.post("/async/pdf/parse")
async def async_parse(file: UploadFile = File(...), callback_url: str = Form(...), user: str = Form(default=None)):
    # 读取file字节流
    return create_pdf_parse_task(file, callback_url, user or DEFAULT_USER)


# 定义回调接口，url中包含pathvariable
@router.post("/async/pdf/parse/callback/{taskNo}")
async def async_parse_callback(taskNo: str = Path(..., title="The task number"), task: dict = Body(...)):
    logging.info("接收回调")
    print(taskNo, task)


# 文件解析 - 监听解析任务，异步解析
@router.on_event("startup")
async def startup_event():
    print("Starting background task...")
    thread = Thread(target=listen_parse_task_layout_and_domtree)
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
