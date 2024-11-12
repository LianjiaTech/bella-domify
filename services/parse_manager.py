# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/11/05
#    @Description   :
#
# ===============================================================
import json

import requests

import multiprocessing

from server.task_executor import s3
from common.tool.chubaofs_tool import ChuBaoFSTool

from services.layout_parser import pptx_parser, docx_parser, pdf_parser, txt_parser, xlsx_parser, xls_parser, csv_parser
from services.domtree_parser import pdf_parser as pdf_domtree_parser
from utils import general_util
from utils.docx2pdf_util import convert_docx_to_pdf_in_memory
from io import IOBase
import io



# 开始解析
DOCUMENT_PARSE_BEGIN = "document_parse_begin"
# layout解析完毕
DOCUMENT_PARSE_LAYOUT_FINISH = "document_parse_layout_finish"
# domtree解析完毕
DOCUMENT_PARSE_DOMTREE_FINISH = "document_parse_domtree_finish"
# 全部解析完毕
DOCUMENT_PARSE_FINISH = "document_parse_finish"


def validate_parameters(file_name, file):
    # 参数检验
    if not file_name:
        raise ValueError("异常：参数为空 file_name")
    if not file:
        raise ValueError("异常：参数为空 file")
    if '.' not in file_name:
        raise ValueError("异常：文件名没有包含后缀")


def layout_parse(file_name: str = None, file: bytes = None):
    # 参数检验
    validate_parameters(file_name, file)
    # 获取文件后缀
    file_extension = general_util.get_file_type(file_name)
    # 根据后缀判断文件类型
    if file_extension == 'pptx':
        return pptx_parser.layout_parse(file)
    elif file_extension == 'pdf':
        return pdf_parser.layout_parse(file)
    elif file_extension == 'docx':
        return docx_parser.layout_parse(file)
    elif file_extension == 'csv':
        return csv_parser.layout_parse(file)
    elif file_extension == 'doc':
        docx_stream = io.BytesIO(file)
        file = convert_docx_to_pdf_in_memory(docx_stream)
        return docx_parser.layout_parse(file)
    elif file_extension == 'xlsx':
        return xlsx_parser.layout_parse(file)
    elif file_extension == 'xls':
        return xls_parser.layout_parse(file)
    elif file_extension in ["txt", "md", "json", "jsonl", "py", "c", "cpp", "java", "js", "sh", "xml", "yaml", "html"]:
        return txt_parser.layout_parse(file)
    else:
        raise ValueError("异常：不支持的文件类型")


def domtree_parse(file_name: str = None, file: bytes = None):
    # 参数检验
    validate_parameters(file_name, file)
    # 获取文件后缀
    file_extension = general_util.get_file_type(file_name)
    # 根据后缀判断文件类型
    if file_extension == 'pdf':
        return pdf_domtree_parser.pdf_parse(file)
    else:
        return []


def worker(func, return_dict, key):
    result = func()
    return_dict[key] = result


# layout解析
def layout_parse_and_callback(file_id, file_name, contents):
    # 获取版面解析结果
    result = layout_parse(file_name, contents)
    # 解析结果存S3

    # 解析完毕回调fileAPI和bella
    callback_file_api(file_id, DOCUMENT_PARSE_LAYOUT_FINISH)
    callback_bella_api(file_id, DOCUMENT_PARSE_LAYOUT_FINISH)


    return result


# domtree解析
def domtree_parse_and_callback(file_id, file_name, contents):
    # 获取domtree解析结果
    result = domtree_parse(file_name, contents)
    # 解析结果存S3

    # 解析完毕回调fileAPI和bella
    callback_file_api(file_id, DOCUMENT_PARSE_DOMTREE_FINISH)
    callback_bella_api(file_id, DOCUMENT_PARSE_LAYOUT_FINISH)

    return result


def parse_result_layout_and_domtree(file_name, stream):
    file_id = "ait-raw-data/1000000030706450/app_data/belle/其他/评测文件8-交易知识15-rag-测试.pdf"

    file_type = ""
    # 读取文件流内容
    contents = stream.read()
    stream.close()

    # 多进程并行解析
    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    p1 = multiprocessing.Process(target=worker, args=(layout_parse_and_callback, (file_id, file_name, contents), return_dict, 'layout_parse'))
    p2 = multiprocessing.Process(target=worker, args=(domtree_parse_and_callback, (file_id, file_name, contents), return_dict, 'domtree_parse'))

    p1.start()
    p2.start()
    p1.join()
    p2.join()

    # 解析完毕回调fileAPI和bella
    callback_file_api(file_id, DOCUMENT_PARSE_FINISH)
    callback_bella_api(file_id, DOCUMENT_PARSE_FINISH)


def get_s3_parse_result(file_name, bytes_stream):
    file_key = s3.upload_file_by_md5(stream=bytes_stream)
    s3_result = s3.get_file_text_content(file_key)
    # json.loads(s3_result)
    return s3_result


def upload_s3_result(bytes_stream):
    file_key = s3.upload_file_by_md5(stream=bytes_stream)
    image_s3_url = s3.get_file_url(file_key)
    pass


def callback_file_api(file_id, status_code):
    postprocessor_name = ""  # todo
    api_key = ""  # todo

    url = f"http://localhost:8080/v1/files/{file_id}/postprocessors/{postprocessor_name}/progress"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "status": "",
        "percent": 20
    }

    response = requests.post(url, headers=headers, json=data)

    print(response.status_code)
    print(response.json())


def callback_bella_api(file_id, status_code):
    postprocessor_name = ""  # todo
    api_key = ""  # todo

    url = f"http://localhost:8080/v1/files/{file_id}/postprocessors/{postprocessor_name}/progress"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "status": "",
        "percent": 20
    }

    response = requests.post(url, headers=headers, json=data)

    print(response.status_code)
    print(response.json())


if __name__ == "__main__":
    chubao = ChuBaoFSTool()
    file_path = "ait-raw-data/1000000030706450/app_data/belle/其他/评测文件8-交易知识15-rag-测试.pdf"
    stream = chubao.read_file(file_path)

    parse_result_layout_and_domtree("评测文件8-交易知识15-rag-测试.pdf", stream)
    # get_s3_parse_result("评测文件8-交易知识15-rag-测试.pdf", stream)

    print()
    # file_type = get_file_type(file_path)
