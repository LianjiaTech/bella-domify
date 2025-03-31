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
import io
import logging
import time

import openai
import requests
from PIL import Image

from server.context import user_context
from server.task_executor import s3

# MODEL_NAME = "ali-qwen2-72b-vl-v1-chat-20250117"
MODEL_NAME = "gpt-4o"


def is_image_large_enough(buf_data, min_size=28):
    """
    检查图像的宽度和高度是否大于指定的最小尺寸。

    参数:
    - buf_data: 图像的二进制数据。
    - min_size: 最小尺寸（默认值为28）。

    返回:
    - 布尔值：如果图像的宽度和高度都大于min_size，则返回True；否则返回False。
    """
    try:
        with Image.open(io.BytesIO(buf_data)) as img:
            width, height = img.size
            return width > min_size and height > min_size
    except Exception as e:
        logging.warning(f"检查图像尺寸失败: {e}")
        return False


def get_file_type(file_path: str) -> str:
    """
    通过文件名，获取文件类型

    Args:
        file_path (str): The file path.

    Returns:
        str: The file type.
    """
    return file_path.split(".")[-1].lower()


def get_pic_url_and_ocr(file, user):
    image_s3_url = ""
    try:
        file_key = s3.upload_file(stream=file)
        image_s3_url = s3.get_file_url(file_key)
        if is_image_large_enough(file):
            ocr_text = llm_image2text(image_s3_url, user)
        else:
            ocr_text = ""
    except Exception as e:
        logging.error(f"pic_parser Exception occurred: {e}")
        ocr_text = ""

    return image_s3_url, ocr_text


def llm_image2text(image_url, user, model=MODEL_NAME, confirm_result=True):
    # return "【ocr功能暂时关闭】"
    if not user:
        logging.error("无法提供ocr内容，原因：user未提供")
        return ""
    if not image_url:
        return ""

    PROMPT = """
    请从图片中提取出表达的信息，注意，只提取文字和结构，禁止修改文字，禁止二次加工，不做描述，以免曲解原意
    
    如果图片中有表格，表格部分可以以markdown方式来表达；对于合并单元格的情况，可以用相同的冗余列来表示，保证表格的行数列数一致；
    如果图片中有流程图，流程图部分可以用mermaid方式表达；
    如果图片中有柱状图、饼图、折线图等这样文字占比很小，无法用文字准确表达含义的部分，直接从枚举值【柱状图、饼图、折线图】等选择一个输出图表类型；
    如果只是段落，直接提取出原文即可；
    如果没有文字，则直接返回‘无文字’；
    """

    max_retry = 3
    response = None
    while max_retry > 0 and response is None:
        max_retry -= 1
        try:
            if max_retry == 0 and confirm_result:
                model = "gpt-4o"  # 最后一次尝试用4o
            logging.info(f"图片信息提取请求LLM中【模型名：{model}】")
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
            logging.info(f"图片信息提取请求LLM中，【请求结果：{response}】")
        except openai.RateLimitError:
            time.sleep(10)
        except requests.exceptions.Timeout:
            logging.error("请求超时")
            break
        except Exception as e:
            logging.error("openai chat error: %s", e)
            break
    if response is None or not response.choices:
        logging.error("图片信息提取请求失败")
        return "[图片OCR失败]"
    ocr_text = response.choices[0].message.content
    if not ocr_text or ocr_text == "无":
        ocr_result = f"[图片OCR内容为空]"
        return ocr_result
    else:
        ocr_text = str(ocr_text)
        ocr_result = \
            f"[图片OCR内容]\n{ocr_text}"
        return ocr_result


if __name__ == "__main__":
    import os


    os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"
    user = "1000000023008327"
    user_context.set(user)

    print(llm_image2text(
        "https://img.ljcdn.com/cv-aigc/d8530cfa14334458b6c5b43e232c483f?ak=Q265N5ELG32TT7UWO8YJ&exp=1733486661&ts=1733483061&sign=9113a47e7dababdd117cef161505ff81",
        "1000000023008327"))
