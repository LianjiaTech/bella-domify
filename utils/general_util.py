# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/7/16
#    @Description   : 
#
# ===============================================================
import logging
import time

import openai
import requests

from server.context import user_context
from server.task_executor import s3

MODEL_NAME = "ali-qwen2-72b-vl-v1-chat-20250117"


def get_file_type(file_path: str) -> str:
    """
    Get the file type from a file path.

    Args:
        file_path (str): The file path.

    Returns:
        str: The file type.
    """
    return file_path.split(".")[-1].lower()


def llm_image2text(image_url, user, model=MODEL_NAME):
    if not user:
        return f"【无法提供ocr内容，原因：user未提供】"
    # return "tmp"

    PROMPT = """
    请从图片中提取出表达的信息，注意只提取信息不做二次加工，不做描述。
    
    如果图片中有表格，可以以markdown格式的表格表达；
    如果图片中有流程图，可以用mermaid方式表达；
    如果图片中有柱状图、饼图、折线图等这样文字占比很小的部分，直接输出‘无’；
    如果只是段落，直接提取出文字即可；
    如果没有文字，则直接返回‘无’；
    """

    max_retry = 2
    response = None
    while max_retry > 0 and response is None:
        try:
            response = openai.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                },
                            },
                        ],
                    }
                ],
                temperature=0.001,
                top_p=0.01,
                model=model,
                user=user,
                timeout=30  # 超时时间为30秒
            )
        except openai.RateLimitError:
            max_retry -= 1
            time.sleep(10)
        except requests.exceptions.Timeout:
            logging.error("请求超时")
            break
        except Exception as e:
            logging.error("openai chat error: %s", e)
            break
    if response is None:
        return f"【图片OCR失败，无内容】"
    ocr_text = response.choices[0].message.content

    if not ocr_text or ocr_text == "无":
        ocr_result = \
            f"""
====【图片OCR内容】====

=====================
                """
        return ocr_result
    else:
        ocr_text = str(ocr_text)
        ocr_result = \
            f"""
====【图片OCR内容】====
{ocr_text}
=====================
        """
        return ocr_result


if __name__ == "__main__":
    import os

    os.environ["OPENAI_API_KEY"] = "qaekDD2hBoZE4ArZZlOQ9fYTQ74Qc8mq"
    os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"
    user = "1000000023008327"
    user_context.set(user)

    print(llm_image2text(
        "https://img.ljcdn.com/cv-aigc/d8530cfa14334458b6c5b43e232c483f?ak=Q265N5ELG32TT7UWO8YJ&exp=1733486661&ts=1733483061&sign=9113a47e7dababdd117cef161505ff81",
        "1000000023008327"))
