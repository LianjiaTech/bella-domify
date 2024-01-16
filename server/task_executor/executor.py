import logging
import time
from typing import Optional

import requests

from pdf2docx import Converter
from pdf2docx.dom_tree.domtree import DomTreeModel
from .db.model import upload_task_parse_res, update_task_status_by_id
from .task_manager import get_pdf_parse_task
from .s3 import get_file, upload_text_content


def execute_parse_task():
    while True:
        task = get_pdf_parse_task()
        if task is None:
            time.sleep(10)
            continue
        dom_tree = parse_pdf_file(task.file_key)
        if dom_tree is None:
            update_task_status_by_id(task.task_id, 'error')
            continue
        time.sleep(2)
        parse_res = dom_tree.model_dump_json()
        parse_file_key = upload_text_content(parse_res)
        upload_task_parse_res(task.task_id, parse_file_key)
        call_back_url = task.callback_url.format(taskNo=task.task_id)
        # 发送post请求，传递dom_tree
        try:
            response = requests.post(call_back_url, json=dom_tree.model_dump())
            if response.status_code != 200:
                logging.error(f"pdf解析回调失败，task_id={task.task_id}, callback_url={call_back_url}, "
                              f"status_code={response.status_code}")
        except Exception as e:
            logging.error(f"pdf解析回调失败，task_id={task.task_id}, callback_url={call_back_url}, error={e}")


def parse_pdf_file(file_key: str) -> Optional[DomTreeModel]:
    try:
        file_content = get_file(file_key)
        converter = Converter(stream=file_content)
        dom_tree = converter.dom_tree_parse(
            remove_watermark=True,
            parse_stream_table=False
        )
        dom_tree = DomTreeModel(dom_tree=dom_tree)
        return dom_tree
    except Exception as e:
        logging.error(f"pdf解析失败，file_key={file_key}, error={e}")
        return None
