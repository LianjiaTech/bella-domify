# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/7/22
#    @Description   : 
#
# ===============================================================

import io
import os
import multiprocessing
import re
import subprocess
from io import IOBase
import logging

import fitz
from services.layout_parser import pdf_parser


lock = multiprocessing.Lock()


def convert_docx_to_pdf_in_memory(docx_stream: IOBase):
    logging.info('convert_docx_to_pdf')
    # 使用 unoconv 将 DOCX 转换为 PDF 并将输出重定向到管道
    with lock:
        process = subprocess.Popen(
            ['unoconv', '-f', 'pdf', '--stdin', '--stdout'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 读取 PDF 数据
        pdf_data, error = process.communicate(input=docx_stream.read())

        if process.returncode != 0:
            raise Exception(f"Conversion failed: {error.decode('utf-8')}")

        # 将 PDF 数据存储在 BytesIO 对象中
        pdf_stream = io.BytesIO(pdf_data)

        if is_mime_email(pdf_stream):
            raise Exception(f"Conversion failed: 不支持非原生的doc格式")

        return pdf_stream


def is_mime_email(pdf_stream):
    pdf_document = fitz.Document(stream=pdf_stream)
    content = pdf_document.load_page(0).get_text()

    # Check for MIME-Version header
    if not re.search(r'^MIME-Version:\s*1\.0', content, re.MULTILINE):
        return False

    # Check for Content-Type header with boundary
    if not re.search(r'^Content-Type:\s*multipart/[^;]+;\s*boundary="[^"]+"', content, re.MULTILINE):
        return False

    # Check for boundary delimiters
    boundary_match = re.search(r'boundary="([^"]+)"', content)
    if not boundary_match:
        return False

    return True


if __name__ == "__main__":

    file_path = os.path.abspath(__file__).split("document_parse")[0] + "document_parse/test/samples/file_type_demo/"
    file_name = 'demo.doc'
    # 示例使用
    with open(file_path + file_name, 'rb') as docx_file:
        docx_stream = io.BytesIO(docx_file.read())

    pdf_stream = convert_docx_to_pdf_in_memory(docx_stream)
    print(pdf_parser.layout_parse(docx_stream))

