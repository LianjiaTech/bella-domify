import logging
import time
import traceback
from typing import Optional
import multiprocessing

import requests

from pdf2docx import Converter
from pdf2docx.dom_tree.domtree import DomTreeModel
from services import parse_manager
from .db.model import upload_task_parse_res
from .task_manager import get_pdf_parse_task, get_kafka_pdf_parse_task
from .s3 import get_file, upload_text_content
from ..context import user_context, DEFAULT_USER


def listen_parse_task_layout_and_domtree():
    while True:
        task = get_kafka_pdf_parse_task()
        try:
            if task is None:
                time.sleep(2)
                continue

            file_id = ""
            file_name = ""

            parse_manager.parse_result_layout_and_domtree(file_id, file_name)
        except Exception as e:
            time.sleep(2)
            logging.error(f"解析任务失败，error={e}")


def worker(func, return_dict, key):
    result = func()
    return_dict[key] = result

def execute_parse_task_layout_and_domtree(task):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    args1 = (1, 2)  # function1的参数
    args2 = (3, 4)  # function2的参数

    p1 = multiprocessing.Process(target=worker, args=(function1, args1, return_dict, 'func1'))
    p2 = multiprocessing.Process(target=worker, args=(function2, args2, return_dict, 'func2'))

    p1.start()
    p2.start()

    p1.join()
    p2.join()


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
