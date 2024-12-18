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
import io
import json
import multiprocessing
import logging

import requests
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

import services.s3_service as s3_service
from common.tool.chubaofs_tool import ChuBaoFSTool
from services.domtree_parser import pdf_parser as pdf_domtree_parser
from services.layout_parser import pptx_parser, docx_parser, pdf_parser, txt_parser, xlsx_parser, xls_parser, \
    csv_parser, pic_parser
from utils import general_util
from utils.docx2pdf_util import convert_docx_to_pdf_in_memory
from services.constants import FILE_API_URL, OPENAI_API_KEY
from server.context import user_context

# 开始解析
DOCUMENT_PARSE_BEGIN = "document_parse_begin"
# layout解析完毕
DOCUMENT_PARSE_LAYOUT_FINISH = "document_parse_layout_finish"
# domtree解析完毕
DOCUMENT_PARSE_DOMTREE_FINISH = "document_parse_domtree_finish"
# 全部解析完毕
DOCUMENT_PARSE_FINISH = "document_parse_finish"
# 解析失败
DOCUMENT_PARSE_FAIL = "document_parse_fail"

percent_map = {
    DOCUMENT_PARSE_BEGIN: 0,
    DOCUMENT_PARSE_LAYOUT_FINISH: 50,
    DOCUMENT_PARSE_DOMTREE_FINISH: 50,
    DOCUMENT_PARSE_FINISH: 100,
    DOCUMENT_PARSE_FAIL: 100,
}

chubao = ChuBaoFSTool()


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
        return pdf_parser.layout_parse(file)
    elif file_extension == 'xlsx':
        return xlsx_parser.layout_parse(file)
    elif file_extension == 'xls':
        return xls_parser.layout_parse(file)
    elif file_extension in ["txt", "md", "json", "jsonl", "py", "c", "cpp", "java", "js", "sh", "xml", "yaml", "html"]:
        return txt_parser.layout_parse(file)
    elif file_extension in ["png", "jpeg", "jpg", "bmp"]:
        return pic_parser.layout_parse(file)
    else:
        raise ValueError("异常：不支持的文件类型")


def domtree_parse(file_name: str = None, file: bytes = None):

    # json转换
    def convert_to_json(obj):
        json_compatible_data = jsonable_encoder(obj)
        json_string = json.dumps(json_compatible_data, ensure_ascii=False, indent=2)
        return json_string, json_compatible_data

    # 参数检验
    validate_parameters(file_name, file)
    # 获取文件后缀
    file_extension = general_util.get_file_type(file_name)
    # 根据后缀判断文件类型
    if file_extension == 'pdf':
        try:
            dom_tree_model = pdf_domtree_parser.pdf_parse(file)
            _, json_compatible_data = convert_to_json(dom_tree_model)
            return True, json_compatible_data
            # return ParserResult(parser_data=json_compatible_data).to_json()
        except Exception as e:
            logging.error('domtree_parse解析失败。[文件类型]pdf [原因]未知 [Exception]:%s', e)
            return False, {}
            # return ParserResult(parser_code=ParserCode.ERROR, parser_msg="非pdf类型或损坏的pdf文件").to_json()

    else:
        return True, {}


def worker(func, args, return_dict, key, user):
    # 在子进程中设置上下文变量的值
    user_context.set(user)
    result = func(*args)
    return_dict[key] = result


# layout解析
def layout_parse_and_callback(file_id, file_name: str, contents: bytes, callbacks: list):
    try:
        # 获取版面解析结果
        layout_parse_result = layout_parse(file_name, contents)
        # 解析失败，直接回调
        if not layout_parse_result:
            callback_after_parse(file_id, DOCUMENT_PARSE_FAIL, callbacks)
            return layout_parse_result

        # 解析结果存S3
        parse_result = {"layout_parse": layout_parse_result, "domtree_parse": {}}
        s3_service.upload_s3_parse_result(file_id, parse_result)
        # 解析完毕回调
        callback_after_parse(file_id, DOCUMENT_PARSE_LAYOUT_FINISH, callbacks)
    except Exception as e:
        print(f"Exception layout_parse_and_callback: {e}")
        return ""
    return layout_parse_result


# domtree解析
def domtree_parse_and_callback(file_id, file_name: str, contents: bytes, callbacks: list):
    try:
        # 获取domtree解析结果
        parse_succeed, parse_result = domtree_parse(file_name, contents)
        # 解析失败，直接回调
        if not parse_succeed:
            callback_after_parse(file_id, DOCUMENT_PARSE_FAIL, callbacks)
            return {}

        # 解析结果存S3
        all_parse_result = {"layout_parse": "", "domtree_parse": parse_result}
        s3_service.upload_s3_parse_result(file_id, all_parse_result)
        # 解析完毕回调
        callback_after_parse(file_id, DOCUMENT_PARSE_DOMTREE_FINISH, callbacks)
    except Exception as e:
        print(f"Exception domtree_parse_and_callback: {e}")
        return {}
    return parse_result


def retrieve_file(file_id):
    url = f"{FILE_API_URL}/v1/files/{file_id}/content"  # todo luxu  try逻辑，如果取不到
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    response = requests.get(url, headers=headers)
    return response.content


def parse_result_layout_and_domtree(file_id, file_name, callbacks: list):

    # 读取文件流内容
    contents = retrieve_file(file_id)

    # # 单进程
    # layout_parse_result = layout_parse(file_name, contents)
    # domtree_parse_result = domtree_parse(file_name, contents)
    # parse_result = {"layout_parse": layout_parse_result, "domtree_parse": domtree_parse_result}

    # 多进程并行解析
    manager = multiprocessing.Manager()
    user = user_context.get()
    return_dict = manager.dict()
    p1 = multiprocessing.Process(target=worker, args=(
        layout_parse_and_callback, (file_id, file_name, contents, callbacks), return_dict, 'layout_parse', user))
    p2 = multiprocessing.Process(target=worker, args=(
        domtree_parse_and_callback, (file_id, file_name, contents, callbacks), return_dict, 'domtree_parse', user))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    parse_result = dict(return_dict)

    # 解析结果存S3
    s3_service.upload_s3_parse_result(file_id, parse_result)
    # 解析完毕回调
    if not parse_result.get("layout_parse") and not parse_result.get("domtree_parse"):
        # 两个解析都没结果，返回失败
        status_code = DOCUMENT_PARSE_FAIL
    else:
        status_code = DOCUMENT_PARSE_FINISH

    callback_after_parse(file_id, status_code, callbacks)

    return parse_result


# 串行接口
def parse_result_layout_and_domtree_sync(file_name, contents):
    layout_parse_result = layout_parse(file_name, contents)
    parse_succeed, domtree_parse_result = domtree_parse(file_name, contents)
    parse_result = {"layout_parse": layout_parse_result, "domtree_parse": domtree_parse_result}
    return parse_result


def callback_after_parse(file_id, status_code, callbacks):
    # 解析完毕回调fileAPI
    callback_file_api(file_id, status_code)
    # 业务方回调
    for callback in callbacks:
        callback_other_api(file_id, status_code, callback)


def callback_file_api(file_id, status_code):
    postprocessor_name = "document_parser"
    url = f"{FILE_API_URL}/v1/files/{file_id}/progress/{postprocessor_name}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "file_id": file_id,
        "status": status_code,
        "message": "",
        "percent": percent_map[status_code]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # 如果响应状态码不是 200，抛出 HTTPError
        print(f"callback_file_api 调用成功 状态:{status_code} 状态码: {response.status_code} 响应内容: {response.json()} ")
        return True

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求异常: {req_err}")
    return False


def callback_other_api(file_id, status_code, callback_url):
    data = {
        "file_id": file_id,
        "status": status_code,
        "message": "",
        "percent": percent_map[status_code]
    }
    try:
        response = requests.post(callback_url, json=data)
        response.raise_for_status()  # 如果响应状态码不是 200，抛出 HTTPError
        print(f"callback_other_api 调用成功 状态:{status_code} 状态码: {response.status_code} 响应内容: {response.json()} ")
        return True

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求异常: {req_err}")
    return False


def api_get_result_service(file_id):
    s3_result = s3_service.get_s3_parse_result(file_id)
    if s3_result:  # 解析结果存在
        return s3_result
    else:
        raise HTTPException(status_code=404, detail="解析结果不存在")


if __name__ == "__main__":
    import os

    os.environ["OPENAI_API_KEY"] = "qaekDD2hBoZE4ArZZlOQ9fYTQ74Qc8mq"
    os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"

    # file_path = "ait-raw-data/1000000030706450/app_data/belle/其他/评测文件8-交易知识15-rag-测试.pdf"
    # file_path = "ait-raw-data/1000000023008327/app_data/belle/默认/《贝壳离职管理制度V3.0》5页.pdf"
    file_path = "ait-raw-data/1000000023008327/app_data/belle/默认/《贝壳入职管理制度》5页.pdf"
    stream = chubao.read_file(file_path)

    parse_result_layout_and_domtree("评测文件8-交易知识15-rag-测试.pdf", stream, [])
    # get_s3_parse_result("评测文件8-交易知识15-rag-测试.pdf", stream)

    print()
    # file_type = get_file_type(file_path)
