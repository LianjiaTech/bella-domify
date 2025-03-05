# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/11/13
#    @Description   : 
#
# ===============================================================
import hashlib
import json
import logging

from server.task_executor import s3
from services.constants import ParseType

PREFIX_PARSE_RESULT = "document_parse_result_"


# 计算md5值
def calculate_md5(stream: bytes) -> str:
    md5_hash = hashlib.md5()
    md5_hash.update(stream)
    return md5_hash.hexdigest()


# 解析结果获取
def get_s3_parse_result(file_id, parse_type=""):
    try:
        file_key = get_file_key_by_file_id(file_id, parse_type)
        s3_result = s3.get_file_text_content(file_key)
        s3_result_json = json.loads(s3_result)
    except Exception as e:
        logging.warning(e)
        return

    return s3_result_json


# 解析结果上传
def upload_s3_parse_result(file_id, parse_result, parse_type=""):
    file_key = get_file_key_by_file_id(file_id, parse_type)
    s3.upload_dict_content(parse_result, file_key)
    logging.info(f"解析结果上传成功 file_key:{file_key}")
    return True


# 根据md5获取文件S3上传名字
def get_parse_result_file_key(stream: bytes = None) -> str:
    file_key = PREFIX_PARSE_RESULT + calculate_md5(stream)
    return file_key


# 根据file_id获取文件S3上传名字
def get_file_key_by_file_id(file_id, parse_type="") -> str:
    # return "document_parse_" + current_version + file_id
    if parse_type in [ParseType.LAYOUT.value, ParseType.DOMTREE.value, ParseType.MARKDOWN.value]:
        return PREFIX_PARSE_RESULT + parse_type + file_id
    else:
        return PREFIX_PARSE_RESULT + file_id


if __name__ == "__main__":
    file_key = "document_parse_result_86bf45d968cb1da2065a4e9fc41e2ef8"
    s3_result = s3.get_file_text_content(file_key)
    s3_result_json = json.loads(s3_result)
    # print(s3_result_json)
