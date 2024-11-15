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
    # return "4o OCR暂时关闭"  # todo luxu
    PROMPT = """
    请从图片中提取出文本信息，非文本信息必须直接忽略。没有文本信息则直接返回‘无’，否则直接输出文字结果。
    """
    url = "https://img.ljcdn.com/cv-aigc/76e9cfcb31ed4e18bb302ba38d6af8ec?ak=Q265N5ELG32TT7UWO8YJ&exp=1730979408&ts=1730975808&sign=b8040a653584e4029f762da0c2dd250d"
    # url =  "https://img.ljcdn.com/cv-aigc/126f24e2bc0f4d2ab94e22b33d68b76f?ak=Q265N5ELG32TT7UWO8YJ&exp=1730981105&ts=1730977505&sign=1d1ff1da9ec59da244c8d408fdcd77fb"

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
                # model="gpt-3.5-turbo",
                user="23008327",  # todo luxu
                # user=user_context.get(),
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
    from server.context import user_context
    user_context.set("1000000023008327")
    print(llm_image2text(""))
