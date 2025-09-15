# -*- coding: utf-8 -*-
"""
文件校验相关的公共函数
"""
from doc_parser.context import logger_context
from server.common.exception import BusinessError

logger = logger_context.get_logger()


def check_file_size(file_info: dict, max_size_mb: int = 20) -> float:
    """
    检查文件大小，返回文件大小(MB)
    
    Args:
        file_info: 文件信息字典，包含 id, bytes, filename 等字段
        max_size_mb: 最大文件大小限制(MB)，默认20MB
        
    Returns:
        float: 文件大小(MB)
        
    Raises:
        BusinessError: 当文件大小超出限制时
    """
    file_id = file_info["id"]
    file_size = file_info["bytes"]
    file_name = file_info["filename"]
    file_size_m = file_size / (1000 * 1000)

    if file_size_m > max_size_mb:
        logger.error(f"文件大小超出限制. file_id:{file_id} file_name:{file_name} file_size:{file_size_m}M")
        raise BusinessError(f"文件大小超出限制({max_size_mb}MB)，处理中止")
    
    return file_size_m