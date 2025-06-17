# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/10/30
#    @Description   : 
#
# ===============================================================
import json

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


def load_json(file_path):
    with open(file_path, 'r') as file:
        # 读取 JSON 数据
        data = json.load(file)
    return data



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


for file_name in file_list:
    file_all_name = f'{file_name}_GT_label.json'
    parser_json = load_json(file_all_name)
    sorted_json = sort_json(parser_json)

    with open(file_all_name, 'w') as json_file:
        json.dump(sorted_json, json_file, indent=2, ensure_ascii=False)

