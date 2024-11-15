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
from settings.ini_config import config
from .db.model import upload_task_parse_res
from .s3 import get_file, upload_text_content
from .task_manager import get_pdf_parse_task
from ..context import user_context, DEFAULT_USER


def listen_parse_task_layout_and_domtree():
    # 配置消费者
    kafka_conf = {
        'bootstrap.servers': config.get('KAFKA', 'servers'),  # Kafka服务器地址
        'group.id': config.get('KAFKA', 'group_id'),  # 消费者组ID
        'auto.offset.reset': 'earliest'  # 从最早的消息开始消费
    }
    # 创建消费者实例
    consumer = Consumer(kafka_conf)
    # 订阅主题
    consumer.subscribe([config.get('KAFKA', 'topic')])  # todo luxu
    try:
        while True:
            # 拉取消息
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                time.sleep(2)
                continue
            if msg.error():
                raise KafkaException(msg.error())

            # 解析消息内容
            message_value = msg.value().decode('utf-8')
            print(f"Received message: {message_value}")

            # 判断是否需要文件解析处理
            try:
                message_json = json.loads(message_value)
                file_id = message_json.get("data", {}).get("id", "")
                file_name = message_json.get("data", {}).get("filename", "")
                user = message_json.get("data", {}).get("filename", "")
                metadata = message_json.get("data", {}).get("metadata", {})
                post_processors = metadata.get("post_processors", [])
                callbacks = metadata.get("post_processors", [])
                if "file_parse" in post_processors:
                    print("Message consumed and offset committed.")
                    user_context.set(user)
                    parse_manager.parse_result_layout_and_domtree(file_id, file_name, callbacks)
                else:
                    print("Message not consumed.")
                consumer.commit(msg)

            except json.JSONDecodeError:
                print("Failed to decode JSON message.")
            except Exception as e:
                print(f"Exception occurred: {e}")
                # # 提交偏移量，标记消息为已处理
                # consumer.commit(msg)

    except KeyboardInterrupt:
        pass
    finally:
        # 关闭消费者
        consumer.close()


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
