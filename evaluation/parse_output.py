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
import logging
import time

from pdf2docx import Converter, parse
from pdf2docx.dom_tree.domtree import DomTreeModel
import json
from fastapi.encoders import jsonable_encoder

from server.context import user_context
user_context.set("1000000023008327")

import os

os.environ["OPENAI_API_KEY"] = "qaekDD2hBoZE4ArZZlOQ9fYTQ74Qc8mq"
os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"

root_dir = os.getcwd().split("document_parse")[0] + "document_parse/"

# 评测集文件名
file_list = [
    # "评测文件1-喵回QA_3页",
    "《贝壳入职管理制度》5页",
    "《贝壳离职管理制度V3.0》5页",
    "中文论文Demo中文文本自动校对综述_4页",
    "自制_4页",
    "花桥学院业务核算指引_6页",
    "英文论文Demo_前3页",
    "评测文件9-博学_13页",
]


def convert_to_json(obj):
    json_compatible_data = jsonable_encoder(obj)
    json_string = json.dumps(json_compatible_data, ensure_ascii=False, indent=4)
    return json_string, json_compatible_data


# 自定义排序函数
def custom_sort(key):
    order = ["order_num", "element", "child",
             "root",
             "block_type", "text", "image_base64_str",
             "rows", "cells",
             "start_row", "end_row", "start_col", "end_col",
             ]
    if key in order:
        return order.index(key)
    else:
        return 9999


# 递归排序函数
def sort_json(data):
    if isinstance(data, dict):
        # 对字典中的每个值递归排序
        sorted_dict = {k: sort_json(v) for k, v in sorted(data.items(), key=lambda item: custom_sort(item[0]))}
        return sorted_dict
    elif isinstance(data, list):
        # 对列表中的每个元素递归排序
        return [sort_json(item) for item in data]
    else:
        # 如果是基本数据类型，直接返回
        return data


def output(dom_tree_model, file_name):
    # 打印 JSON，使用自定义排序函数
    _, json_compatible_data = convert_to_json(dom_tree_model)
    sorted_data = sort_json(json_compatible_data)
    json_string = json.dumps(sorted_data, ensure_ascii=False, indent=4)

    # print(json_string)

    json_dir = root_dir + "evaluation/parse_json/beike/"
    with open(json_dir + file_name + '_beike.json', 'w', encoding='utf-8') as file:
        # json.dump(sorted_data, file, indent=4, ensure_ascii=False)
        # print(sorted_data)
        json_str = json.dumps(sorted_data, ensure_ascii=False, separators=(',', ':'))

        file.write(json_str)


def parse():
    documents_dir = root_dir + "evaluation/documents/"

    for file_name in file_list:

        converter = Converter(documents_dir + file_name + ".pdf")
        dom_tree = converter.dom_tree_parse(
            # start=0, end=10,    # 相当于[start:end]，前算，后不算
            remove_watermark=True,
            debug=True,
            debug_file_name=documents_dir + file_name + "-debug.pdf",
            parse_stream_table=False,
            filter_catalog=False,  # 默认会过滤 False:不过滤
            filter_cover=False,    # 默认会过滤 False:不过滤
        )

        dom_tree_model = DomTreeModel(dom_tree=dom_tree)

        output(dom_tree_model, file_name)
        print(f"解析完毕：{file_name}")


if __name__ == "__main__":
    parse()
