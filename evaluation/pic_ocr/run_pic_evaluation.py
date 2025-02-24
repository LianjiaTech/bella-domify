# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/9/11
#    @Description   :
#
# ===============================================================
import copy
import datetime
import json
import logging
import os
import re
from collections import defaultdict
from difflib import SequenceMatcher
from statistics import mean

import fitz
import markdown
import pandas as pd
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from shapely.geometry import box
import logging
import time

import openai
import json
import requests

from server.context import user_context
from server.task_executor import s3

from utils.general_util import llm_image2text


def clean_string(input_string):
    # 去除标点符号和空格、换行符、制表符
    cleaned_string = re.sub(r'[^\w]', '', input_string)
    return cleaned_string


file_names_list = [
    "1文字类-1纯文字图片1.png",
    "1文字类-2SQL命令图片.png",
    "1文字类-3博学封面.png",
    "2表格类-1普通表格1.png",
    "2表格类-2合并单元格的表.png",
    "2表格类-3三线表图.png",
    "3纯文字提取无意义类-1柱状图.png",
    "3纯文字提取无意义类-2流程图.png",
    "3纯文字提取无意义类-3饼图.png",
    "3纯文字提取无意义类-4架构图.png",
    "3纯文字提取无意义类-5软件界面截图.png",
    "3纯文字提取无意义类-6风景图.png",
    "4布局复杂类-1单页ppt瓷砖踢脚线.png",
]

pic_path = "pic/"


def load_json(file_path):
    with open(file_path, 'r') as file:
        # 读取 JSON 数据
        data = json.load(file)
    return data


def get_ocr_result(model_name):

    output_txt_file_path = f"ocr_result_{model_name}.txt"
    output_json_file_path = f"ocr_result_{model_name}.json"

    result_json = {}

    with open(output_txt_file_path, 'w') as output_file:
        for pic_name in file_names_list:
            print(pic_name)
            file_path = pic_path + pic_name

            # 打开文件并读取为二进制流
            with open(file_path, 'rb') as file_stream:
                # 上传文件到 S3
                file_key = s3.upload_file(stream=file_stream)

                # 获取文件的 S3 URL
                image_s3_url = s3.get_file_url(file_key)

                ocr_res = llm_image2text(image_s3_url, user, model_name, False)

                result_json[pic_name] = ocr_res

                # 将 URL 写入文本文件
                output_file.write("-------------------------" + pic_name + '\n' + ocr_res + '\n\n')

    with open(output_json_file_path, 'w') as output_json_file:
        # 将 URL 写入文本文件
        json_str = json.dumps(result_json, ensure_ascii=False, separators=(',', ':'))
        # 注意 这里直接输出的json和label结构不同，需要调整
        output_json_file.write(json_str)


def evaluation(model_name):
    parser_json = load_json(f"ocr_result_{model_name}.json")
    label_json = load_json("pic_label.json")

    results = []

    for file_name, label_data in label_json.items():
        parser_text = parser_json.get(file_name, "")
        content_list = label_data["content"]
        content_all = len(content_list)
        content_right = 0
        if not content_list:
            results.append({
                "file_name": file_name,
                "content_right": content_right,
                "content_all": content_all,
                "ratio": 1
            })
            continue

        for content in content_list:
            content_filtered = clean_string(content)
            parser_filtered = clean_string(parser_text)
            if content_filtered in parser_filtered:
                content_right += 1
            else:
                print("-------")
                print("file_name:", file_name)
                print("content_filtered:", content_filtered)
                print("parser_filtered:", parser_filtered)

        ratio = content_right / content_all if content_all > 0 else 0
        results.append({
            "file_name": file_name,
            "content_right": content_right,
            "content_all": content_all,
            "ratio": ratio
        })

    df = pd.DataFrame(results)

    # 计算纵向求和
    total_content_right = df["content_right"].sum()
    total_content_all = df["content_all"].sum()
    total_ratio = total_content_right / total_content_all if total_content_all > 0 else 0

    # 添加总计行
    total_row = {
        "file_name": "总计",
        "content_right": total_content_right,
        "content_all": total_content_all,
        "ratio": total_ratio
    }
    # 使用 pd.concat 代替 append
    total_row_df = pd.DataFrame([total_row])
    df = pd.concat([df, total_row_df], ignore_index=True)
    print(df)
    return df


if __name__ == "__main__":
    import os
    os.environ["OPENAI_API_KEY"] = "qaekDD2hBoZE4ArZZlOQ9fYTQ74Qc8mq"
    os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"
    user = "1000000023008327"
    user_context.set(user)

    # from server.task_executor import s3
    #
    # with open('/Users/lucio/Downloads/瓷砖踢脚线4.png', 'rb') as file:
    #     image_bytes = file.read()
    #
    # file_key = s3.upload_file(stream=image_bytes)
    # image_s3_url = s3.get_file_url(file_key)
    #
    # print(image_s3_url)

    # print(llm_image2text(
    #     "https://img.ljcdn.com/cv-aigc/d8530cfa14334458b6c5b43e232c483f?ak=Q265N5ELG32TT7UWO8YJ&exp=1733486661&ts=1733483061&sign=9113a47e7dababdd117cef161505ff81",
    #     "1000000023008327", confirm_result=False))

    model_name = "gpt-4o"
    # model_name = "ali-qwen2-72b-vl-v1-chat-20250117"  # 稳定的线上版本

    # model_name = "doubao-vision-pro-32k"
    # model_name = "ali-qwen2-72b-qwen2vl-v1-chat-20241104"  # 不稳定的

    # model_name = "qwen-vl-max"
    # model_name = "qwen-vl-plus"  # 无法查看您提到的图片

    get_ocr_result(model_name)
    result_df = evaluation(model_name)

