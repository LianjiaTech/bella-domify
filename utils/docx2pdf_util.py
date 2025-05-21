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
import logging
import multiprocessing
import re
import subprocess
from io import IOBase

import fitz

lock = multiprocessing.Lock()


def convert_docx_to_pdf_in_memory(docx_stream: IOBase):
    logging.info('Starting DOCX to PDF conversion')

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
                logging.error("Conversion failed: Process timed out after 60 seconds")
                return

            if process.returncode != 0:
                logging.error(f"Conversion failed: {error.decode('utf-8')}")
                return

            pdf_stream = io.BytesIO(pdf_data)

            if is_mime_email(pdf_stream):
                logging.error("Conversion failed: 不支持非原生的doc格式")
                return

            logging.info('Conversion successful')
            return pdf_stream

    except Exception as e:
        logging.error(f"Conversion failed: {str(e)}")
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

