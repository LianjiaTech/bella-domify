# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/11/14
#    @Description   : 
#
# ===============================================================

import logging

from services.SimpleBlock import SimpleBlock
from services.constants import IMAGE
from services.layout_parse_utils import get_s3_links_for_simple_block_batch
from utils.general_util import get_pic_url_and_ocr
from server.context import user_context


def layout_parse(file):
    try:
        image_s3_url, ocr_text = get_pic_url_and_ocr(file, user_context.get())
    except Exception as e:
        logging.error(f"pic_parser Exception occurred: {e}")
        ocr_text = ""

    result_text = ocr_text
    result_json = get_s3_links_for_simple_block_batch([SimpleBlock(type=IMAGE, ocr_text=ocr_text)])
    return result_json, result_text


if __name__ == "__main__":

    import os
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"
    user_context.set("1000000023008327")

    file_path = os.path.abspath(__file__).split("document_parse")[0] + "document_parse/test/samples/file_type_demo/"

    # file_name = 'demo.txt'
    file_name = 'demo.png'

    # 读取本地文件
    try:
        with open(file_path + file_name, 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        print(f"读取文件失败: {e}")

    print(layout_parse(buf_data))
