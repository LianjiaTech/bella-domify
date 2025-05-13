# fastapi定义接口
import json
import logging
from typing import Optional

from ait_openapi import validate_token
from ait_openapi.exception import AuthorizationException
from fastapi import APIRouter, Header, HTTPException
from fastapi import File, UploadFile
from fastapi import Form, Path, Query

from server.log.log_config import log_config
from services import parse_manager
from .context import user_context

log_config()  # 初始化日志配置

router = APIRouter(prefix="/v1/parser")
health_router = APIRouter(prefix="/actuator/health")


@router.get("/")
async def root():
    return {"message": "Welcome to the Document Parser API"}


@health_router.get("/liveness")
async def health_liveness():
    return {"status": "UP"}


@health_router.get("/readiness")
async def health_readiness():
    return {"status": "UP"}


# 获取结构信息和字符串信息(直接串行解析)
@router.post("/document/parse")
async def document_parse(file_object: UploadFile = File(...),
                         user: str = Form(default=None), parse_type: str = Form(default="all"),
                         strategy: str = Form(default=""),
                         authorization: Optional[str] = Header("", alias="Authorization")):
    try:
        validate_token(authorization)
    except AuthorizationException as e:
        logging.error(f"Authorization failed: {e}")
        return {"error": "Authorization failed", "message": str(e)}

    if not user:
        # 400错误，用户为空
        raise HTTPException(status_code=400, detail="User is required")

    user_context.set(user)
    # 读取file字节流
    file_name = file_object.filename
    contents = await file_object.read()
    strategy_dict = json.loads(strategy) if strategy else {}
    return parse_manager.parse_doc(file_name, contents, parse_type, strategy_dict)


# 获取S3缓存结果: 通过file_id获取解析结果（结构信息和字符串信息）
@router.get("/document/parse/{file_id}")
async def document_parse(file_id: str = Path(...), parse_type: str = Query(default="all"),
                         authorization: Optional[str] = Header("", alias="Authorization")):
    try:
        validate_token(authorization)
    except AuthorizationException as e:
        logging.error(f"Authorization failed: {e}")
        return {"error": "Authorization failed", "message": str(e)}
    return parse_manager.api_get_result_service(file_id, parse_type)
