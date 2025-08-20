# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu
#    @Create Time   : 2024/7/22
#    @Description   : 
#
# ===============================================================

import io
import multiprocessing
import re
import subprocess
from io import IOBase

import fitz

from doc_parser.context import logger_context

logger = logger_context.get_logger()
lock = multiprocessing.Lock()


def convert_docx_to_pdf(file_name: str, contents: bytes):
    """
    将 DOCX 文件转换为 PDF 流

    Args:
        file_name: 文件名
        contents: 文件内容

    Returns:
        tuple: (pdf_stream, modified_file_name)
    """
    # 转换 DOCX 到 PDF
    docx_stream = io.BytesIO(contents)
    pdf_stream = convert_docx_to_pdf_in_memory(docx_stream)

    if not pdf_stream:
        logger.error(f"PDF转换失败 file_name:{file_name}")
        return None, file_name

    logger.info(f"PDF转换成功，准备解析 file_name:{file_name}")

    # 修改文件名后缀为.pdf
    pdf_file_name = file_name.rsplit('.', 1)[0] + '.pdf'
    logger.info(f"文件名已修改 {file_name}-> {pdf_file_name}")

    return pdf_stream, pdf_file_name

def convert_docx_to_pdf_in_memory(docx_stream: IOBase):
    logger.info('Starting DOCX to PDF conversion')

    try:

        with lock:
            process = subprocess.Popen(
                ['unoconv', '-f', 'pdf', '--stdin', '--stdout'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                pdf_data, error = process.communicate(input=docx_stream.read(), timeout=60)
            except subprocess.TimeoutExpired:
                process.kill()
                logger.error("Conversion failed: Process timed out after 60 seconds")
                return

            if process.returncode != 0:
                logger.error(f"Conversion failed: {error.decode('utf-8')}")
                return

            pdf_stream = io.BytesIO(pdf_data)

            if is_mime_email(pdf_stream):
                logger.error("Conversion failed: 不支持非原生的doc格式")
                return

            logger.info('Conversion successful')
            return pdf_stream

    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        return


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

