# -*- coding: utf-8 -*-
import json
from services.parse_manager import DOCX_TO_PDF_FAIL
from doc_parser.context import logger_context, parser_context
from server.common.exception import BusinessError
from server.common.file_validation import check_file_size
from services import parse_manager
from utils import general_util

logger = logger_context.get_logger()

def docx2pdf_task_callback(payload: dict, consumer_info: dict) -> bool:
    """
    专门处理 DOCX2PDF 转换任务的回调函数
    
    Args:
        payload: file api消息体
        consumer_info: 消费者信息
        
    Returns:
        bool: 处理是否成功
    """
    logger.info(f'receive docx2pdf task from file api : {json.dumps(payload)}')
    data = payload.get('data')

    # 监听文件创建和更新事件
    event = payload.get('event')
    if not data or event not in ["file.created", "file.updated"]:
        return True

    # 只处理purpose为assistants类型的文件
    if data.get('purpose') != 'assistants':
        logger.info(f"File {data.get('id')} purpose is not 'assistants': {data.get('purpose')}")
        return True

    # 对于file.updated事件，只关注文件内容修改
    if event == "file.updated" and payload.get('scope') != 'content':
        return True

    # 检查metadata是否为dict类型
    metadata = {}
    try:
        if payload.get('metadata'):
            metadata = json.loads(payload.get('metadata'))
    except json.JSONDecodeError as e:
        logger.error(f"File {data.get('id')} metadata JSONDecodeError")
        return True

    if not isinstance(metadata, dict):
        logger.info(f"File {data.get('id')} metadata is not dict type: {type(metadata)}")
        return True

    file_id = data.get("id", "")
    file_name = data.get("filename", "")
    callbacks = metadata.get("callbacks", [])

    # 检查文件类型，确保是 DOCX/DOC
    if not check_docx_file_type(file_name):
        logger.warning(f"docx2pdf task received non-docx file: {file_name}")
        return True

    # 获取文件信息
    file_info = parse_manager.file_api_get_file_info(file_id)
    if not file_info or "error" in file_info:
        logger.error(f"file_info not found for file_id: {file_id}")
        return True

    # 设置用户上下文
    parser_context.register_user(str(data.get("cuid", "")))
    
    # 检查文件大小（使用公共函数）
    try:
        check_file_size(file_info)
    except BusinessError as e:
        logger.error(f"File {file_id} size check failed: {e}")
        parse_manager.callback_file_api(file_id, DOCX_TO_PDF_FAIL, str(e))
        return True

    # 构建文件元数据
    file_meta = {
        "space_code": data.get("space_code", ""),
        "cuid": data.get("cuid", ""),
        "cu_name": data.get("cu_name", "")
    }
    file_info["file_meta"] = file_meta

    # 执行 DOCX2PDF 转换任务
    logger.info(f"docx2pdf任务开始. file_id:{file_id} file_name:{file_name}")
    parse_manager.convert_docx_to_pdf_task(file_info, callbacks)
    
    return True


def check_docx_file_type(file_name: str) -> bool:
    """检查是否为 DOCX/DOC 文件类型"""
    if "." not in file_name:
        return False
    file_extension = general_util.get_file_type(file_name)
    return file_extension in ['doc', 'docx']