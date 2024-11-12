# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/11/8
#    @Description   : 
#
# ===============================================================

from services.layout_parser import txt_parser

if __name__ == "__main__":

    # file_name = 'demo.txt'
    file_name = 'demo.md'
    # file_name = 'demo.json'
    # file_name = 'demo.jsonl'
    # file_name = 'demo.py'
    # file_name = 'demo.c'
    # file_name = 'demo.cpp'
    # file_name = 'demo.java'
    # file_name = 'demo.js'
    # file_name = 'demo.SH'
    # file_name = 'demo.XML'
    # file_name = 'demo.YAML'

    # 读取本地文件
    try:
        with open(file_name, 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        print(f"读取文件失败: {e}")

    print(txt_parser.layout_parse(buf_data))

