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

from doc_parser.context import logger_context, parser_context
from doc_parser.dom_parser.parsers.excel.converter import XlsxExcelConverter, XlsExcelConverter
from doc_parser.dom_parser.parsers.pdf.converter import PDFConverter
from doc_parser.dom_parser.parsers.txt.converter import TxtConverter
from doc_parser.layout_parser import pdf_parser, xlsx_parser, csv_parser, pic_parser
from doc_parser.layout_parser import pptx_parser, txt_parser, xls_parser, docx_parser
from server.protocol.standard_domtree import StandardDomTree
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


def convert_docx_to_pdf_stream(file_name: str, contents: bytes):
    """
    将 DOCX 文件转换为 PDF 流
    
    Args:
        file_name: 文件名
        contents: 文件内容
        
    Returns:
        tuple: (pdf_stream, modified_file_name)
    """
    # 转换 DOCX 到 PDF
    docx_stream = io.BytesIO(contents)
    pdf_stream = convert_docx_to_pdf_in_memory(docx_stream)
    
    if not pdf_stream:
        logger.error(f"PDF转换失败 file_name:{file_name}")
        return None, file_name
    
    logger.info(f"PDF转换成功，准备解析 file_name:{file_name}")
    
    # 修改文件名后缀为.pdf
    modified_file_name = file_name.rsplit('.', 1)[0] + '.pdf'
    logger.info(f"文件名已修改 {file_name}-> {modified_file_name}")
    
    return pdf_stream, modified_file_name


def validate_parameters(file_name, file):
    # 参数检验
    if not file_name:
        raise ValueError("异常：参数为空 file_name")
    if not file:
        raise ValueError("异常：参数为空 file")
    if '.' not in file_name:
        raise ValueError("异常：文件名没有包含后缀")


def layout_parse(file_name: str = None, file: bytes = None, task_id=""):
    # 获取文件后缀
    file_extension = general_util.get_file_type(file_name)
    logging.info(f'layout_parse解析开始 文件名：{file_name}')

    # 根据后缀判断文件类型
    if file_extension == 'pptx':
        result_json, result_text = pptx_parser.layout_parse(file)
    elif file_extension == 'pdf':
        result_json, result_text = pdf_parser.layout_parse(file)
    elif file_extension == 'docx':
        result_json, result_text = docx_parser.layout_parse(file)
    elif file_extension == 'csv':
        result_json, result_text = csv_parser.layout_parse(file)
    elif file_extension == 'xlsx':
        result_json, result_text = xlsx_parser.layout_parse(file)
    elif file_extension == 'xls':
        result_json, result_text = xls_parser.layout_parse(file)
    elif file_extension in ["txt", "md", "json", "jsonl", "py", "c", "cpp", "java", "js", "sh", "xml", "yaml", "html"]:
        result_json, result_text = txt_parser.layout_parse(file)
    elif file_extension in ["png", "jpeg", "jpg", "bmp"]:
        result_json, result_text = pic_parser.layout_parse(file)
    else:
        raise ValueError("异常：不支持的文件类型")
    logging.info(f'layout_parse解析完毕 文件名：{file_name}')

    # 缓存结果
    if task_id:
        s3_service.upload_s3_parse_result(task_id, result_json, ParseType.LAYOUT.value)

    return result_json, result_text


def domtree_parse(file_name: str = None, file: bytes = None, task_id="", check_faq=True):
    # 获取缓存
    s3_result_domtree = s3_service.get_s3_parse_result(task_id, ParseType.DOMTREE.value)
    s3_result_markdown = s3_service.get_s3_parse_result(task_id, ParseType.MARKDOWN.value)
    if s3_result_domtree and s3_result_markdown:
        logging.info(f'缓存获取成功 file_id：{task_id}')
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


    # 根据后缀判断文件类型
    if file_extension == 'pdf':
        try:
            dom_tree_model, markdown_res = pdf_domtree_parser.pdf_parse(file, check_faq)
            _, json_compatible_data = convert_to_json(dom_tree_model)
            logging.info(f'domtree_parse解析完毕 文件名：{file_name}')

            if task_id:
                s3_service.upload_s3_parse_result(task_id, json_compatible_data, ParseType.DOMTREE.value)
                s3_service.upload_s3_parse_result(task_id, markdown_res, ParseType.MARKDOWN.value)

            return True, json_compatible_data, markdown_res
        except Exception as e:
            logging.error('domtree_parse解析失败。[文件类型]pdf [原因]未知 [Exception]:%s', e)
            return False, {}, ""
    elif file_extension == 'csv' or file_extension == 'txt':
        converter = TxtConverter(stream=file)
        txt_dom_tree = converter.dom_tree_parse()
        _, json_compatible_data = convert_to_json(txt_dom_tree)
        txt_markdown = txt_dom_tree.to_markdown()
        if task_id and parser_context.parse_result_cache_provider:
            parser_context.parse_result_cache_provider.upload_parse_result(task_id, json_compatible_data,
                                                                           ParseType.DOMTREE.value)
            parser_context.parse_result_cache_provider.upload_parse_result(task_id, txt_markdown,
                                                                           ParseType.MARKDOWN.value)
        return True, json_compatible_data, txt_markdown
    elif file_extension == 'xlsx':
        converter = XlsxExcelConverter(stream=file)
        xlsx_dom_tree = converter.dom_tree_parse()
        _, json_compatible_data = convert_to_json(xlsx_dom_tree)
        xlsx_markdown = xlsx_dom_tree.to_markdown()
        if task_id and parser_context.parse_result_cache_provider:
            parser_context.parse_result_cache_provider.upload_parse_result(task_id, json_compatible_data, ParseType.DOMTREE.value)
            parser_context.parse_result_cache_provider.upload_parse_result(task_id, xlsx_markdown, ParseType.MARKDOWN.value)
        return True, json_compatible_data, xlsx_markdown
    elif file_extension == 'xls':
        converter = XlsExcelConverter(stream=file)
        xls_dom_tree = converter.dom_tree_parse()
        _, json_compatible_data = convert_to_json(xls_dom_tree)
        xls_markdown = xls_dom_tree.to_markdown()
        if task_id and parser_context.parse_result_cache_provider:
            parser_context.parse_result_cache_provider.upload_parse_result(task_id, json_compatible_data,
                                                                           ParseType.DOMTREE.value)
            parser_context.parse_result_cache_provider.upload_parse_result(task_id, xls_markdown,
                                                                           ParseType.MARKDOWN.value)
        return True, json_compatible_data, xls_markdown

    else:
        raise ValueError("异常：不支持的文件类型")


def worker(func, args, return_dict, key, user):
    # 在子进程中设置上下文变量的值
    user_context.set(user)
    result = func(*args)
    return_dict[key] = result


# layout解析
def layout_parse_and_callback(file_id, file_name: str, contents: bytes, callbacks: list, user: str = None, parser_context_param=None):
    try:
        parser_context.register_all(parser_context_param)
        parser_context.register_user(user)
        # 获取版面解析结果
        layout_result_json, layout_result_text = layout_parse(file_name, contents, file_id)
        # 解析失败，直接回调
        if not layout_result_json:
            callback_parse_progress(file_id, DOCUMENT_PARSE_FAIL, callbacks)
            return layout_result_text

        s3_service.upload_s3_parse_result(file_id, layout_result_json, ParseType.LAYOUT.value)
        # 解析完毕回调
        callback_parse_progress(file_id, DOCUMENT_PARSE_LAYOUT_FINISH, callbacks)
    except Exception as e:
        callback_file_api(file_id, 'failed', str(e))
        logging.info(f"Exception layout_parse_and_callback: {e}")
        return ""
    return layout_result_text, layout_result_json


# domtree解析
def domtree_parse_and_callback(file_id, file_name: str, contents: bytes, callbacks: list, user: str = None,  parser_context_param=None):
    try:
        parser_context.register_all(parser_context_param)
        parser_context.register_user(user)
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
        s3_service.upload_s3_parse_result(file_id, parse_result, ParseType.DOMTREE.value)
        s3_service.upload_s3_parse_result(file_id, markdown_res, ParseType.MARKDOWN.value)
        # 解析完毕回调
        callback_parse_progress(file_id, DOCUMENT_PARSE_DOMTREE_FINISH, callbacks)
    except Exception as e:
        callback_file_api(file_id, 'failed', str(e))
        logging.info(f"Exception domtree_parse_and_callback: {e}")
        return {}
    return parse_result, markdown_res


# 从FileAPI获取文件
def file_api_retrieve_file(file_id):
    url = f"{FILE_API_URL}/v1/files/{file_id}/content"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    response = requests.get(url, headers=headers)
    return response.content


# 从FileAPI获取文件名称
def file_api_get_file_info(file_id):
    url = f"{FILE_API_URL}/v1/files/{file_id}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    response = requests.get(url, headers=headers)
    response_data = json.loads(response.content)
    return response_data


def file_api_upload_domtree(io, file_id):
    """
    向 file_api 上传文件的 dom-tree

    Args:
        io: 文件内容（二进制）
        file_id: 文件ID

    Returns:
        响应数据
    """
    url = f"{FILE_API_URL}/v1/files/dom-tree"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    # 发送请求
    response = requests.post(
    url,
    files={
        "file": io
    },
    data={"file_id": file_id},
    headers=headers,
)

    # 解析响应
    try:
        response_data = json.loads(response.content)
        return response_data
    except json.JSONDecodeError:
        return {"error": {"message": response.content, "type": "Failed to decode response"}}


def file_api_upload_pdf(pdf_stream: io.BytesIO, file_id: str) -> dict:
    """
    向 file_api 上传 PDF 文件
    
    Args:
        pdf_stream: PDF 文件流
        file_id: 文件ID
        
    Returns:
        响应数据
    """
    url = f"{FILE_API_URL}/v1/files/pdf"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    
    # 重置流位置到开始
    pdf_stream.seek(0)
    
    # 发送请求
    response = requests.post(
        url,
        files={
            "file": ("document.pdf", pdf_stream, "application/pdf")
        },
        data={"file_id": file_id},
        headers=headers,
    )
    
    # 解析响应
    try:
        response_data = json.loads(response.content)
        return response_data
    except json.JSONDecodeError:
        return {"error": {"message": response.content, "type": "Failed to decode response"}}


def parse_result_layout_and_domtree(file_info, callbacks: list):
    file_id = file_info["id"]
    file_name = file_info["filename"]
    logger.info(f"parse_result_layout_and_domtree 开始解析 file_id:{file_id}")
    start_time = time.time()

    callback_parse_progress(file_id, DOCUMENT_PARSE_BEGIN, callbacks)
    # 读取文件流内容
    contents = file_api_retrieve_file(file_id)
    
    # 检查是否需要转换
    file_extension = general_util.get_file_type(file_name)
    pdf_stream = None

    if file_extension in ['doc', 'docx']:
        pdf_stream, file_name = convert_docx_to_pdf_stream(file_name, contents)
        
        # 如果是 DOCX 转换的 PDF，回流到 API
        if pdf_stream:
            pdf_upload_result = file_api_upload_pdf(pdf_stream, file_id)
            if not pdf_upload_result or "error" in pdf_upload_result:
                logger.warning(f"PDF回流失败 file_id:{file_id}, 错误信息: {pdf_upload_result.get('error', '未知错误')}")
            else:
                logger.info(f"PDF回流成功 file_id:{file_id}")
            
            pdf_stream.seek(0)

    # 多进程并行解析
    manager = Manager()
    user = user_context.get()
    return_dict = manager.dict()

    parse_contents = pdf_stream if pdf_stream else contents

    p1 = multiprocessing.Process(target=worker, args=(
        layout_parse_and_callback, (file_id, file_name, parse_contents, callbacks, parser_context.get_user(), parser_context), return_dict, 'layout_parse'))
    p2 = multiprocessing.Process(target=worker, args=(
        domtree_parse_and_callback, (file_id, file_name, parse_contents, callbacks, parser_context.get_user(), parser_context), return_dict, 'domtree_parse'))
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

    parse_result_raw = dict(return_dict)

    layout_result = parse_result_raw["layout_parse"][1] if parse_result_raw["layout_parse"] else None
    domtree_result = parse_result_raw["domtree_parse"][0] if parse_result_raw["domtree_parse"] else None
    markdown_result = parse_result_raw["domtree_parse"][1] if parse_result_raw["domtree_parse"] else None

    # 解析结果存S3
    s3_service.upload_s3_parse_result(file_id, layout_result, ParseType.LAYOUT.value)
    s3_service.upload_s3_parse_result(file_id, domtree_result, ParseType.DOMTREE.value)
    s3_service.upload_s3_parse_result(file_id, markdown_result, ParseType.MARKDOWN.value)

    # 解析完毕回调
    if not layout_result and not domtree_result:
        # 两个解析都没结果，返回失败
        status_code = DOCUMENT_PARSE_FAIL
    else:
        status_code = DOCUMENT_PARSE_FINISH

    if domtree_result:
        # 如果有domtree结果转换为协议标准化的StandardDomTree
        standard_dom_tree = StandardDomTree.from_domtree_dict(domtree=domtree_result, file_info=file_info)
        standard_dom_tree_json = jsonable_encoder(standard_dom_tree.root)
        upload_result = file_api_upload_domtree(file_id=file_id, io=io.StringIO(json.dumps(standard_dom_tree_json, ensure_ascii=False)))
        if not upload_result or "error" in upload_result:
            raise Exception(f"上传domtree到file_api失败 file_id:{file_id}, 错误信息: {upload_result.get('error', '未知错误')}")
        logger.info(f"上传domtree到file_api成功 file_id:{file_id}")

    callback_parse_progress(file_id, status_code, callbacks)

    # 记录结束时间并计算总耗时
    end_time = time.time()
    total_time = end_time - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    logging.info(f"parse_result_layout_and_domtree 完成解析 file_id:{file_id}, 总耗时: {minutes}分钟{seconds}秒")
    return {
        "layout_result": layout_result,
        "domtree_result": domtree_result,
        "markdown_result": markdown_result,
    }


# 同步解析接口(file_name)
def parse_doc(file_name, contents: bytes, parse_type, strategy: dict):
    # 对文件名和文件内容进行md5加密，task_id主要是为了cache
    task_id = general_util.unified_md5(file_name, contents, parse_type, strategy)

    # 检查是否需要转换
    file_extension = general_util.get_file_type(file_name)
    pdf_stream = None
    if file_extension in ['doc', 'docx']:
        pdf_stream, file_name = convert_docx_to_pdf_stream(file_name, contents)

    parse_contents = pdf_stream if pdf_stream else contents

    parse_type_res = parse_type + "_result"
    # 定义解析函数映射
    parse_functions = {
        "layout_result": lambda file_name, contents: layout_parse(file_name, contents, task_id)[0],
        # 只返回layout_result_json
        "domtree_result": lambda file_name, contents: domtree_parse(file_name, contents, task_id, check_faq)[1],
        # 只返回domtree_parse_result
        "markdown_result": lambda file_name, contents: domtree_parse(file_name, contents, task_id, check_faq)[2],
        # 只返回markdown_res
        "all_result": lambda file_name, contents: {
            "layout_result": layout_parse(file_name, contents, task_id)[0],
            "domtree_result": domtree_parse(file_name, contents, task_id, check_faq)[1],
            "markdown_result": domtree_parse(file_name, contents, task_id, check_faq)[2],
        }
    }

    # 检查parse_type是否有效
    if parse_type_res not in parse_functions:
        raise HTTPException(
            status_code=404,
            detail="parse_type传参异常，枚举值范围[domtree, layout, markdown, all]"
        )

    # 根据parse_type_res选择解析函数并执行
    parse_result = parse_functions[parse_type_res](file_name, parse_contents)
    # 返回结果
    ret = parse_result if parse_type_res == "all_result" else {parse_type_res: parse_result}
    # 返回task_id
    ret["task_id"] = task_id
    return ret


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
        logging.info(
            f"callback_file_api 调用成功 状态:{status_code} 状态码: {response.status_code} 响应内容: {response.json()} ")
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
        logging.info(
            f"callback_other_api 调用成功 状态:{status_code} 状态码: {response.status_code} 响应内容: {response.json()} ")
        return True

    except requests.exceptions.HTTPError as http_err:
        logging.info(f"HTTP 错误: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logging.info(f"请求异常: {req_err}")
    return False


def api_get_result_service(file_id, parse_type="all"):
    if parse_type == ParseType.All.value:
        layout_cache = s3_service.get_s3_parse_result(file_id, ParseType.LAYOUT.value)
        domtree_cache = s3_service.get_s3_parse_result(file_id, ParseType.DOMTREE.value)
        markdown_cache = s3_service.get_s3_parse_result(file_id, ParseType.MARKDOWN.value)
        if not layout_cache and not domtree_cache and not markdown_cache:
            raise HTTPException(status_code=404, detail="解析结果不存在")
        return {
            "layout_result": layout_cache,
            "domtree_result": domtree_cache,
            "markdown_result": markdown_cache
        }

    s3_result = s3_service.get_s3_parse_result(file_id, parse_type)
    if not s3_result:  # 解析结果不存在
        raise HTTPException(status_code=404, detail="解析结果不存在")

def pdf_parse(contents: bytes = None):
    converter = PDFConverter(stream=contents)
    dom_tree = converter.dom_tree_parse(
        remove_watermark=True,
        parse_stream_table=False
    )
    return dom_tree, dom_tree.to_markdown()

