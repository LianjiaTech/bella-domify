import json

from doc_parser.context import logger_context
from utils.s3 import get_file_text_content, upload_dict_content

PREFIX_PARSE_RESULT = "document_parse_result_"

logger = logger_context.get_logger()

# 解析结果获取
def get_s3_parse_result(file_id, parse_type=""):
    try:
        file_key = get_file_key_by_file_id(file_id, parse_type)
        s3_result = get_file_text_content(file_key)
        s3_result_json = json.loads(s3_result)
    except Exception as e:
        logger.warning(e)
        return

    return s3_result_json


# 解析结果上传
def upload_s3_parse_result(file_id, parse_result, parse_type):
    file_key = get_file_key_by_file_id(file_id, parse_type)
    upload_dict_content(parse_result, file_key)
    logger.info(f"解析结果上传成功 file_key:{file_key}")
    return True


# 根据file_id获取文件S3上传名字
def get_file_key_by_file_id(file_id, parse_type="") -> str:
    return PREFIX_PARSE_RESULT + parse_type + file_id