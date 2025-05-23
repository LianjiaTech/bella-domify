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
import csv
import os
from io import BytesIO, StringIO

from services.constants import TEXT
from services.layout_parse_utils import get_s3_links_for_simple_block_batch
from services.simple_block import SimpleBlock


def layout_parse(file):
    # 尝试将二进制文件内容解码为文本
    charsets = ['gbk', 'utf-8', 'utf-8-sig', 'latin1', 'iso-8859-1']
    for charset in charsets:
        try:
            input_stream = BytesIO(file)
            input_stream = StringIO(input_stream.read().decode(charset))
            csv_reader = csv.reader(input_stream)

            lines = []
            for record in csv_reader:
                line = ",".join(record).replace("\n", "\u2028")
                lines.append(line)

            result_text = "\n".join(lines) + "\n"
            result_json = get_s3_links_for_simple_block_batch([SimpleBlock(type=TEXT, text=result_text)])
            return result_json, result_text

        except UnicodeDecodeError:
            continue

    raise ValueError("异常：文件内容无法解码为支持的字符集")


def markdown_parse(file):
    # 尝试将二进制文件内容解码为文本
    charsets = ['utf-8', 'gbk', 'utf-8-sig', 'latin1', 'iso-8859-1']
    for charset in charsets:
        try:
            input_stream = BytesIO(file)
            input_stream = StringIO(input_stream.read().decode(charset))
            csv_reader = csv.reader(input_stream)

            # 读取CSV内容并转换为Markdown表格
            lines = []
            for i, record in enumerate(csv_reader):
                if i == 1:  # 在第二行添加分隔线
                    lines.append("| " + " | ".join(["---"] * len(record)) + " |")
                lines.append("| " + " | ".join(record) + " |")

            # 将列表转换为字符串并返回
            return "\n".join(lines)

        except UnicodeDecodeError:
            continue
    raise ValueError("无法解码文件内容")


if __name__ == "__main__":

    file_path = os.path.abspath(__file__).split("document_parse")[0] + "document_parse/test/samples/file_type_demo/"

    file_name = 'demo.csv'

    # 读取本地文件
    try:
        with open(file_path + file_name, 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        print(f"读取文件失败: {e}")

    print(layout_parse(buf_data))
