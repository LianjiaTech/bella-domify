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
from io import BytesIO, StringIO
import os


def layout_parse(file):
    # 尝试将二进制文件内容解码为文本
    charsets = ['gbk', 'utf-8', 'utf-8-sig', 'latin1', 'iso-8859-1']
    for charset in charsets:
        print(charset)
        try:
            input_stream = BytesIO(file)
            input_stream = StringIO(input_stream.read().decode(charset))
            csv_reader = csv.reader(input_stream)

            lines = []
            for record in csv_reader:
                line = ",".join(record).replace("\n", "\u2028")
                lines.append(line)

            return "\n".join(lines) + "\n"
        except UnicodeDecodeError:
            continue

    raise ValueError("异常：文件内容无法解码为支持的字符集")


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
