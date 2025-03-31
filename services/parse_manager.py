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
import logging
import multiprocessing
import time
from multiprocessing import Manager

import requests
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

import services.s3_service as s3_service
from common.tool.chubaofs_tool import ChuBaoFSTool
from server.context import user_context
from services.constants import OPENAI_API_KEY
from services.constants import ParseType
from services.domtree_parser import pdf_parser as pdf_domtree_parser
from services.layout_parser import pptx_parser, docx_parser, pdf_parser, txt_parser, xlsx_parser, xls_parser, \
    csv_parser, pic_parser
from settings.ini_config import config
from utils import general_util
from utils.docx2pdf_util import convert_docx_to_pdf_in_memory

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

FILE_API_URL = config.get('FILEAPI', 'URL')


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


def layout_parse(file_name: str = None, file: bytes = None, file_id=""):
    # 获取文件后缀
    file_extension = general_util.get_file_type(file_name)
    logging.info(f'layout_parse解析开始 文件名：{file_name}')

    # # layout的缓存，待result_text下线后添加
    # s3_result = s3_service.get_s3_parse_result(file_id, ParseType.LAYOUT.value)
    # if s3_result:
    #     return s3_result, result_text

    # 根据后缀判断文件类型
    if file_extension == 'pptx':
        result_json, result_text = pptx_parser.layout_parse(file)
    elif file_extension == 'pdf':
        result_json, result_text = pdf_parser.layout_parse(file)
    elif file_extension == 'docx':
        result_json, result_text = docx_parser.layout_parse(file)
    elif file_extension == 'csv':
        result_json, result_text = csv_parser.layout_parse(file)
    elif file_extension == 'doc':
        docx_stream = io.BytesIO(file)
        file = convert_docx_to_pdf_in_memory(docx_stream)
        result_json, result_text = pdf_parser.layout_parse(file)
    elif file_extension == 'xlsx':
        result_json, result_text = xlsx_parser.layout_parse(file)
    elif file_extension == 'xls':
        result_json, result_text = xls_parser.layout_parse(file)
    elif file_extension in ["txt", "md", "json", "jsonl", "py", "c", "cpp", "java", "js", "sh", "xml", "yaml", "html"]:
        result_json, result_text = txt_parser.layout_parse(file)
    elif file_extension in ["png", "jpeg", "jpg", "bmp"]:
        result_json, result_text = pic_parser.layout_parse(file)
    else:
        callback_file_api(file_id, 'failed', '异常：不支持的文件类型')
        raise ValueError("异常：不支持的文件类型")
    logging.info(f'layout_parse解析完毕 文件名：{file_name}')

    # 缓存结果
    if file_id:
        s3_service.upload_s3_parse_result(file_id, result_json, ParseType.LAYOUT.value)

    return result_json, result_text


def domtree_parse(file_name: str = None, file: bytes = None, file_id="", check_faq=True):

    # 获取缓存
    s3_result_domtree = s3_service.get_s3_parse_result(file_id, ParseType.DOMTREE.value)
    s3_result_markdown = s3_service.get_s3_parse_result(file_id, ParseType.MARKDOWN.value)
    if s3_result_domtree and s3_result_markdown:
        logging.info(f'缓存获取成功 file_id：{file_id}')
        return True, s3_result_domtree, s3_result_markdown

    # json转换
    def convert_to_json(obj):
        json_compatible_data = jsonable_encoder(obj)
        json_string = json.dumps(json_compatible_data, ensure_ascii=False, indent=2)
        return json_string, json_compatible_data

    # 参数检验
    validate_parameters(file_name, file)
    # 获取文件后缀
    file_extension = general_util.get_file_type(file_name)
    logging.info(f'domtree_parse解析开始 文件名：{file_name}')

    # 如果是doc、docx文件，转pdf处理
    if file_extension in ['doc', 'docx']:
        docx_stream = io.BytesIO(file)
        file = convert_docx_to_pdf_in_memory(docx_stream)
        file_extension = 'pdf'

    # 根据后缀判断文件类型
    if file_extension == 'pdf':
        try:
            dom_tree_model, markdown_res = pdf_domtree_parser.pdf_parse(file, check_faq)
            _, json_compatible_data = convert_to_json(dom_tree_model)
            logging.info(f'domtree_parse解析完毕 文件名：{file_name}')

            if file_id:
                s3_service.upload_s3_parse_result(file_id, json_compatible_data, ParseType.DOMTREE.value)
                s3_service.upload_s3_parse_result(file_id, markdown_res, ParseType.MARKDOWN.value)

            return True, json_compatible_data, markdown_res
            # return ParserResult(parser_data=json_compatible_data).to_json()
        except Exception as e:
            logging.error('domtree_parse解析失败。[文件类型]pdf [原因]未知 [Exception]:%s', e)
            return False, {}, ""
            # return ParserResult(parser_code=ParserCode.ERROR, parser_msg="非pdf类型或损坏的pdf文件").to_json()
    elif file_extension == 'csv':
        markdown_res = csv_parser.markdown_parse(file)
        if file_id:
            s3_service.upload_s3_parse_result(file_id, markdown_res, ParseType.MARKDOWN.value)
        return True, {}, markdown_res
    elif file_extension == 'xlsx':
        markdown_res = xlsx_parser.markdown_parse(file)
        if file_id:
            s3_service.upload_s3_parse_result(file_id, markdown_res, ParseType.MARKDOWN.value)
        return True, {}, markdown_res
    elif file_extension == 'xls':
        markdown_res = xls_parser.markdown_parse(file)
        if file_id:
            s3_service.upload_s3_parse_result(file_id, markdown_res, ParseType.MARKDOWN.value)
        return True, {}, markdown_res

    else:
        return True, {}, ""


def worker(func, args, return_dict, key, user):
    # 在子进程中设置上下文变量的值
    user_context.set(user)
    result = func(*args)
    return_dict[key] = result


# layout解析
def layout_parse_and_callback(file_id, file_name: str, contents: bytes, callbacks: list):
    try:
        # 获取版面解析结果
        layout_result_json, layout_result_text = layout_parse(file_name, contents, file_id)
        # 解析失败，直接回调
        if not layout_result_json:
            callback_parse_progress(file_id, DOCUMENT_PARSE_FAIL, callbacks)
            return layout_result_text

        # 解析结果存S3
        parse_result = {
            # 冗余字段
            "layout_parse": layout_result_text,
            "layout_parse_json": layout_result_json,
            "domtree_parse": {},
            # 最终字段
            "layout_result": layout_result_json,
            "domtree_result": {},
            "markdown_result": "",
        }
        s3_service.upload_s3_parse_result(file_id, parse_result)
        # 解析完毕回调
        callback_parse_progress(file_id, DOCUMENT_PARSE_LAYOUT_FINISH, callbacks)
    except Exception as e:
        logging.info(f"Exception layout_parse_and_callback: {e}")
        return ""
    return layout_result_text, layout_result_json


# domtree解析
def domtree_parse_and_callback(file_id, file_name: str, contents: bytes, callbacks: list):
    try:
        # 获取domtree解析结果
        parse_succeed, parse_result, markdown_res = domtree_parse(file_name, contents, file_id)
        # 解析失败，直接回调
        if not parse_succeed:
            callback_parse_progress(file_id, DOCUMENT_PARSE_FAIL, callbacks)
            return {}

        if not parse_result and not markdown_res:
            # 无解析结果，不上报
            return {}

        # 解析结果存S3
        all_parse_result = {
            # 冗余字段
            "layout_parse": "",
            "layout_parse_json": [],
            "domtree_parse": parse_result,
            # 最终字段
            "layout_result": [],
            "domtree_result": parse_result,
            "markdown_result": markdown_res
        }
        s3_service.upload_s3_parse_result(file_id, all_parse_result)
        # 解析完毕回调
        callback_parse_progress(file_id, DOCUMENT_PARSE_DOMTREE_FINISH, callbacks)
    except Exception as e:
        logging.info(f"Exception domtree_parse_and_callback: {e}")
        return {}
    return parse_result, markdown_res


# 从FileAPI获取文件
def file_api_retrieve_file(file_id):
    url = f"{FILE_API_URL}/v1/files/{file_id}/content"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    response = requests.get(url, headers=headers)
    return response.content


# 从FileAPI获取文件名称 todo 删除
def file_api_get_file_name(file_id):
    url = f"{FILE_API_URL}/v1/files/{file_id}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    response = requests.get(url, headers=headers)
    response_data = json.loads(response.content)
    file_name = response_data["filename"]
    return file_name


# 从FileAPI获取文件名称
def file_api_get_file_info(file_id):
    url = f"{FILE_API_URL}/v1/files/{file_id}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    response = requests.get(url, headers=headers)
    response_data = json.loads(response.content)
    return response_data


def parse_result_layout_and_domtree(file_id, file_name, callbacks: list):
    logging.info(f"parse_result_layout_and_domtree 开始解析 file_id:{file_id}")
    start_time = time.time()

    callback_parse_progress(file_id, DOCUMENT_PARSE_BEGIN, callbacks)
    # 读取文件流内容
    contents = file_api_retrieve_file(file_id)

    # 多进程并行解析
    manager = Manager()
    user = user_context.get()
    return_dict = manager.dict()
    p1 = multiprocessing.Process(target=worker, args=(
        layout_parse_and_callback, (file_id, file_name, contents, callbacks), return_dict, 'layout_parse', user))
    p2 = multiprocessing.Process(target=worker, args=(
        domtree_parse_and_callback, (file_id, file_name, contents, callbacks), return_dict, 'domtree_parse', user))
    p1.start()
    p2.start()

    # 设置超时时间（例如 60 秒）
    timeout = 60 * 15  # 15min

    # 等待子进程完成，超时后终止子进程
    p1.join(timeout)
    if p1.is_alive():
        p1.terminate()
        p1.join()
        logging.error(f"layout_parse 子进程超时并已终止 file_id:{file_id}")
        return

    p2.join(timeout)
    if p2.is_alive():
        p2.terminate()
        p2.join()
        logging.error(f"domtree_parse 子进程超时并已终止 file_id:{file_id}")
        return

    # todo 临时保留冗余字段
    # parse_result = dict(return_dict)

    parse_result_raw = dict(return_dict)
    parse_result = {
        # 冗余字段
        "layout_parse": parse_result_raw["layout_parse"][0] if parse_result_raw["layout_parse"] else None,
        "layout_parse_json": parse_result_raw["layout_parse"][1] if parse_result_raw["layout_parse"] else None,
        "domtree_parse": parse_result_raw["domtree_parse"][0] if parse_result_raw["domtree_parse"] else None,
        # 最终字段
        "layout_result": parse_result_raw["layout_parse"][1] if parse_result_raw["layout_parse"] else None,
        "domtree_result": parse_result_raw["domtree_parse"][0] if parse_result_raw["domtree_parse"] else None,
        "markdown_result": parse_result_raw["domtree_parse"][1] if parse_result_raw["domtree_parse"] else None
    }

    # 解析结果存S3
    s3_service.upload_s3_parse_result(file_id, parse_result)
    # 解析完毕回调
    if not parse_result.get("layout_parse") and not parse_result.get("domtree_parse"):
        # 两个解析都没结果，返回失败
        status_code = DOCUMENT_PARSE_FAIL
    else:
        status_code = DOCUMENT_PARSE_FINISH

    callback_parse_progress(file_id, status_code, callbacks)

    # 记录结束时间并计算总耗时
    end_time = time.time()
    total_time = end_time - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    logging.info(f"parse_result_layout_and_domtree 完成解析 file_id:{file_id}, 总耗时: {minutes}分钟{seconds}秒")
    return parse_result


# 同步解析接口(file_name)
def parse_result_layout_and_domtree_sync(file_name, contents):
    layout_result_json, layout_result_text = layout_parse(file_name, contents)
    parse_succeed, domtree_parse_result, markdown_res = domtree_parse(file_name, contents)
    parse_result = {
        "layout_parse": layout_result_text,
        "layout_parse_json": layout_result_json,
        "domtree_parse": domtree_parse_result,

        "layout_result": layout_result_json,
        "domtree_result": domtree_parse_result,
        "markdown_result": markdown_res,
    }
    return parse_result


# 同步解析接口(file_id)
def parse_layout_and_domtree_sync_by_file_id(file_id, parse_type="", check_faq=True):
    parse_type_res = parse_type + "_result"
    # 定义解析函数映射
    parse_functions = {
        "layout_result": lambda file_name, contents: layout_parse(file_name, contents, file_id)[0],  # 只返回layout_result_json
        "domtree_result": lambda file_name, contents: domtree_parse(file_name, contents, file_id, check_faq)[1],  # 只返回domtree_parse_result
        "markdown_result": lambda file_name, contents: domtree_parse(file_name, contents, file_id, check_faq)[2],  # 只返回markdown_res
        "all_result": lambda file_name, contents: {
            "layout_result": layout_parse(file_name, contents, file_id)[0],
            "domtree_result": domtree_parse(file_name, contents, file_id, check_faq)[1],
            "markdown_result": domtree_parse(file_name, contents, file_id, check_faq)[2],
        }
    }

    # 检查parse_type是否有效
    if parse_type_res not in parse_functions:
        raise HTTPException(
            status_code=404,
            detail="parse_type传参异常，枚举值范围[domtree, layout, markdown, all]"
        )

    # 获取文件内容和文件名
    contents = file_api_retrieve_file(file_id)
    file_name = file_api_get_file_name(file_id)

    # 根据parse_type_res选择解析函数并执行
    parse_result = parse_functions[parse_type_res](file_name, contents)
    print(parse_result)
    # 返回结果
    return parse_result if parse_type_res == "all_result" else {parse_type_res: parse_result}


def callback_parse_progress(file_id, status_code, callbacks):
    # 解析完毕回调fileAPI
    callback_file_api(file_id, status_code)
    # 业务方回调
    for callback in callbacks:
        callback_other_api(file_id, status_code, callback)


def callback_file_api(file_id, status_code, message: str = ""):
    postprocessor_name = "document_parser"
    url = f"{FILE_API_URL}/v1/files/{file_id}/progress/{postprocessor_name}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "file_id": file_id,
        "status": status_code,
        "message": message,
        "percent": percent_map.get(status_code, 0)
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # 如果响应状态码不是 200，抛出 HTTPError
        logging.info(f"callback_file_api 调用成功 状态:{status_code} 状态码: {response.status_code} 响应内容: {response.json()} ")
        return True

    except requests.exceptions.HTTPError as http_err:
        logging.info(f"HTTP 错误: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logging.info(f"请求异常: {req_err}")
    return False


def callback_other_api(file_id, status_code, callback_url, message: str = ""):
    data = {
        "file_id": file_id,
        "status": status_code,
        "message": message,
        "percent": percent_map.get(status_code, 0)
    }
    try:
        response = requests.post(callback_url, json=data)
        response.raise_for_status()  # 如果响应状态码不是 200，抛出 HTTPError
        logging.info(f"callback_other_api 调用成功 状态:{status_code} 状态码: {response.status_code} 响应内容: {response.json()} ")
        return True

    except requests.exceptions.HTTPError as http_err:
        logging.info(f"HTTP 错误: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logging.info(f"请求异常: {req_err}")
    return False


def api_get_result_service(file_id, parse_type=""):
    s3_result = s3_service.get_s3_parse_result(file_id)
    if not s3_result:  # 解析结果不存在
        raise HTTPException(status_code=404, detail="解析结果不存在")

    if parse_type == ParseType.All.value:
        return s3_result
    elif parse_type == ParseType.DOMTREE.value:
        parse_result = s3_result.get(parse_type + "_result", [])
    elif parse_type == ParseType.LAYOUT.value:
        parse_result = s3_result.get(parse_type + "_result", {})
    elif parse_type == ParseType.MARKDOWN.value:
        parse_result = s3_result.get(parse_type + "_result", "")
    else:  # 异常逻辑
        raise HTTPException(status_code=404,
                            detail="parse_type传参异常，枚举值范围[domtree, layout, markdown, all]")
    return {parse_type: parse_result}


if __name__ == "__main__":
    import os


    os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"

    user_context.set("1000000023008327")

    parse_result_layout_and_domtree("file-2503181430240024000345-2075695711", "433.txt", [])
    # file_path = "ait-raw-data/1000000030706450/app_data/belle/其他/评测文件8-交易知识15-rag-测试.pdf"
    # file_path = "ait-raw-data/1000000023008327/app_data/belle/默认/《贝壳离职管理制度V3.0》5页.pdf"
    # file_path = "ait-raw-data/1000000023008327/app_data/belle/默认/《贝壳入职管理制度》5页.pdf"
    # stream = chubao.read_file(file_path)
    #
    # print(parse_result_layout_and_domtree("file-2501151703350022000005-277459125", "demo.pptx", []))
    # print(parse_result_layout_and_domtree("file-2501151734460022000006-277459125", "《贝壳入职管理制度》5页.pdf", []))
    # # get_s3_parse_result("评测文件8-交易知识15-rag-测试.pdf", stream)
    #
    # # file_type = get_file_type(file_path)
    #
    # print(file_api_get_file_name("file-2502180943250024000009-277459125"))

