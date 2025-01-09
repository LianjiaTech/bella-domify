# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/11/7
#    @Description   :
#
# ===============================================================
import os

from services.SimpleBlock import SimpleBlock
from services.constants import TEXT
from services.layout_parse_utils import get_s3_links_for_simple_block_batch


def layout_parse(file):
    try:
        text = file.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("异常：文件内容无法解码为 UTF-8 文本")

    result_text = text
    result_json = get_s3_links_for_simple_block_batch([SimpleBlock(type=TEXT, text=result_text)])
    return result_json, result_text


if __name__ == "__main__":

    file_path = os.path.abspath(__file__).split("document_parse")[0] + "document_parse/test/samples/file_type_demo/"

    # file_name = 'demo.txt'
    # file_name = 'demo.md'
    # file_name = 'demo.json'
    # file_name = 'demo.jsonl'
    # file_name = 'demo.py'
    # file_name = 'demo.c'
    # file_name = 'demo.cpp'
    # file_name = 'demo.java'
    # file_name = 'demo.js'
    # file_name = 'demo.sh'
    # file_name = 'demo.xml'
    # file_name = 'demo.yaml'
    file_name = 'demo.html'

    # 读取本地文件
    try:
        with open(file_path + file_name, 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        print(f"读取文件失败: {e}")

    print(layout_parse(buf_data))
