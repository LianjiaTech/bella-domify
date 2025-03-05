import json
import logging
import time
import traceback
from typing import Optional

import requests
from confluent_kafka import Consumer, KafkaException

from pdf2docx import Converter
from pdf2docx.dom_tree.domtree import DomTreeModel
from services import parse_manager
from services.constants import GROUP_ID_LONG_TASK, GROUP_ID_IMAGE_TASK, GROUP_ID_SHORT_TASK
from services.layout_parser import pptx_parser, docx_parser, pdf_parser
from settings.ini_config import config
from utils import general_util
from .db.model import upload_task_parse_res
from .s3 import get_file, upload_text_content
from .task_manager import get_pdf_parse_task
from ..context import user_context, DEFAULT_USER


def listen_parse_task_layout_and_domtree(parser_group_id=""):
    # 配置消费者
    kafka_conf = {
        'bootstrap.servers': config.get('KAFKA', 'servers'),  # Kafka服务器地址
        'group.id': parser_group_id,  # 消费者组ID
        'auto.offset.reset': 'earliest',  # 从最早的消息开始消费
    }
    # 创建消费者实例
    consumer = Consumer(kafka_conf)
    # 订阅主题
    consumer.subscribe([config.get('KAFKA', 'topic')])
    try:
        while True:
            # 拉取消息
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                time.sleep(2)
                logging.info(f"{parser_group_id} msg is None")
                continue
            if msg.error():
                raise KafkaException(msg.error())

            # 解析消息内容
            message_value = msg.value().decode('utf-8')
            logging.info(f"{parser_group_id} Received message: {message_value}")

            # 判断是否需要文件解析处理
            try:
                message_json = json.loads(message_value)
                file_id = message_json.get("data", {}).get("id", "")
                file_name = message_json.get("data", {}).get("filename", "")
                metadata = json.loads(message_json.get("metadata", {}))
                user = metadata.get("user", "")
                if not user:
                    raise ValueError("user为空, 无法进行文件解析")
                user_context.set(user)
                post_processors = metadata.get("post_processors", [])
                callbacks = metadata.get("callbacks", [])
                if "file_parse" in post_processors:
                    contents = parse_manager.file_api_retrieve_file(file_id)
                    file_info = parse_manager.file_api_get_file_info(file_id)
                    # 检查文档准入标准
                    group_id_analysis_info = check_file_size_and_pages(contents, file_info)
                    # 计算groupId
                    file_group_id = get_group_id(group_id_analysis_info)
                    logging.info(f"计算groupId结果. file_id:{file_id} file_name:{file_name} file_group_id:{file_group_id}")

                    if parser_group_id == file_group_id:
                        logging.info(f"parser开始解析. file_id:{file_id} file_group_id:{file_group_id}")
                        parse_manager.parse_result_layout_and_domtree(file_id, file_name, callbacks)

                consumer.commit(msg)

            except json.JSONDecodeError:
                logging.error("Failed to decode JSON message.")
                consumer.commit(msg)
            except Exception as e:
                logging.error(f"Exception occurred: {e}")
                consumer.commit(msg)

    except KeyboardInterrupt:
        pass
    finally:
        # 关闭消费者
        consumer.close()


def check_file_size_and_pages(contents, file_info):
    file_id = file_info["id"]
    file_size = file_info["bytes"]
    file_name = file_info["filename"]
    file_size_m = file_size / (1000 * 1000)  # 文件大小（单位M）
    # 参数检验
    parse_manager.validate_parameters(file_name, contents)
    # 获取文件后缀
    file_extension = general_util.get_file_type(file_name)

    # 文件大小限制：小于20M
    if file_size_m > 20:
        logging.error(f"文件大小超出限制. file_id:{file_id} file_name:{file_name} file_size:{file_size_m}M")
        raise ValueError("文件大小超出限制，解析中止")

    # 文件页数限制：小于5000页
    page_count = 0
    if file_extension == 'pptx':
        page_count = pptx_parser.get_page_count(contents)
    elif file_extension == 'pdf':
        page_count = pdf_parser.get_page_count(contents)
    elif file_extension == 'docx':
        paragraph_count = docx_parser.get_paragraph_count(contents)
        page_count = paragraph_count / 10  # docx文件无法直接拿到页数，先用每页段落数较大值预估
    if page_count > 5000:
        logging.error(f"文件页数超出限制. file_id:{file_id} file_name:{file_name} page_count:{page_count}")
        raise ValueError("文件页数超出限制，解析中止")

    group_id_analysis_info = {
        "file_size_m": file_size_m,
        "file_extension": file_extension,
        "page_count": page_count
    }
    return group_id_analysis_info


def get_group_id(group_id_analysis_info):
    file_size_m = group_id_analysis_info["file_size_m"]
    file_extension = group_id_analysis_info["file_extension"]
    page_count = group_id_analysis_info["page_count"]

    if file_size_m > 8:
        return GROUP_ID_LONG_TASK

    if page_count > 30:
        return GROUP_ID_LONG_TASK

    if file_extension in ["png", "jpeg", "jpg", "bmp"]:
        return GROUP_ID_IMAGE_TASK

    return GROUP_ID_SHORT_TASK


def worker(func, return_dict, key):
    result = func()
    return_dict[key] = result


def execute_parse_task():
    while True:
        task = get_pdf_parse_task()
        try:
            if task is None:
                time.sleep(2)
                continue
            execute_pdf_parse_task(task)
        except Exception as e:
            time.sleep(2)
            logging.error(f"解析任务失败，error={e}")


def execute_pdf_parse_task(task):
    call_back_url = None
    try:
        user_context.set(task.user or DEFAULT_USER)
        call_back_url = task.callback_url.format(taskNo=task.task_id)
        dom_tree = parse_pdf_file(task.file_key)
        parse_res = dom_tree.model_dump_json()
        parse_file_key = upload_text_content(parse_res)
        upload_task_parse_res(task.task_id, 'done', parse_file_key)
        # 发送post请求，传递dom_tree
        call_back(task.task_id, call_back_url, dom_tree.model_dump())
    except Exception:
        logging.error("pdf解析失败", exc_info=True)
        parse_file_key = upload_text_content(traceback.format_exc())
        upload_task_parse_res(task.task_id, 'error', parse_file_key)
        if call_back_url is not None:
            call_back(task.task_id, call_back_url, {})
    finally:
        user_context.clear()


def call_back(task_id, callback_url, json_body):
    # 发送post请求，传递dom_tree
    try:
        response = requests.post(callback_url, json=json_body)
        if response.status_code != 200:
            logging.error(f"pdf解析回调失败，task_id={task_id}, callback_url={callback_url}, "
                          f"status_code={response.status_code}")
    except Exception as e:
        logging.error(f"pdf解析回调失败，task_id={task_id}, callback_url={callback_url}, error={e}")


def parse_pdf_file(file_key: str) -> Optional[DomTreeModel]:
    file_content = get_file(file_key)
    converter = Converter(stream=file_content)
    dom_tree = converter.dom_tree_parse(
        remove_watermark=True,
        parse_stream_table=False
    )
    dom_tree = DomTreeModel(dom_tree=dom_tree)
    return dom_tree
