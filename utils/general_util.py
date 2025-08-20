# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu
#    @Create Time   : 2024/7/16
#    @Description   : 
#
# ===============================================================
import hashlib
import json
from typing import Union
import chardet

def get_file_type(file_path: str) -> str:
    """
    通过文件名，获取文件类型

    Args:
        file_path (str): The file path.

    Returns:
        str: The file type.
    """
    return file_path.split(".")[-1].lower()

def detect_encoding(byte_str: Union[bytes, bytearray]) -> str:
    """
    得到文件编码
    """
    result = chardet.detect(byte_str)
    encoding = result['encoding']
    return encoding

def unified_md5(filename: str, contents: bytes, parst_type: str, strategy: dict) -> str:
    """
    将文件名和文件内容合并计算一个统一的MD5值

    参数:
        filename: 文件名(str)
        content: 文件内容(bytes)
        parst_type: 解析类型(str)
        strategy: 解析策略(dict)

    返回:
        统一的MD5哈希值(16进制字符串)
    """
    md5 = hashlib.md5()

    # 先更新文件名(转换为UTF-8编码的bytes)
    md5.update(filename.encode('utf-8'))

    # 再更新文件内容
    md5.update(contents)

    # 更新解析类型
    md5.update(parst_type.encode('utf-8'))

    # 更新解析策略
    if strategy:
        strategy_str = json.dumps(strategy, ensure_ascii=False).encode('utf-8')
        md5.update(strategy_str)

    return md5.hexdigest()
