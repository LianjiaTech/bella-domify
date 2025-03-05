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
import xlrd
from io import BytesIO
import os
import io
from docx import Document
import mammoth
import docx2txt


def layout_parse(file_bytes):
    with io.BytesIO(file_bytes) as file_stream:
        with open('temp.doc', 'wb') as temp_file:
            temp_file.write(file_stream.read())
        text = docx2txt.process('temp.doc')
    return text


if __name__ == "__main__":

    file_path = os.path.abspath(__file__).split("document_parse")[0] + "document_parse/test/samples/file_type_demo/"

    file_name = 'demo.doc'

    # 读取本地文件
    try:
        with open(file_path + file_name, 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        print(f"读取文件失败: {e}")

    print(layout_parse(buf_data))
