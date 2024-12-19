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
import openai
import time
import logging
import requests
from server.context import user_context


def get_file_type(file_path: str) -> str:
    """
    Get the file type from a file path.

    Args:
        file_path (str): The file path.

    Returns:
        str: The file type.
    """
    return file_path.split(".")[-1].lower()


def llm_image2text(image_url):
    PROMPT = """
    请从图片中提取出文本信息，非文本信息必须直接忽略。没有文本信息则直接返回‘无’，否则直接输出文字结果。
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
                model="gpt-4o",
                user=user_context.get(),
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

    if ocr_text == "无":
        return "【图片OCR无内容】"
    else:
        ocr_text = str(ocr_text)
        ocr_result = \
            f"""
【图片OCR内容】
=====================
{ocr_text}
=====================
        """
        return ocr_result


if __name__ == "__main__":
    import os
    os.environ["OPENAI_API_KEY"] = "qaekDD2hBoZE4ArZZlOQ9fYTQ74Qc8mq"
    os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"
    # user_context.set("1000000023008327")

    # from server.task_executor import s3
    #
    # with open('/Users/lucio/Downloads/瓷砖踢脚线4.png', 'rb') as file:
    #     image_bytes = file.read()
    #
    # file_key = s3.upload_file(stream=image_bytes)
    # image_s3_url = s3.get_file_url(file_key)
    #
    # print(image_s3_url)
    print(llm_image2text("https://img.ljcdn.com/cv-aigc/d8530cfa14334458b6c5b43e232c483f?ak=Q265N5ELG32TT7UWO8YJ&exp=1733486661&ts=1733483061&sign=9113a47e7dababdd117cef161505ff81"))
