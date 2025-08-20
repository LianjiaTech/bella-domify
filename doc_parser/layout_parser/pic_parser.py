# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu
#    @Create Time   : 2024/11/14
#    @Description   : 
#
# ===============================================================

import logging

from doc_parser.context import parser_context
from doc_parser.layout_parser.layout.simple_block import SimpleBlock
from services.constants import IMAGE
from services.layout_parse_utils import get_s3_links_for_simple_block_batch


def layout_parse(image):
    try:
        image_url, ocr_text = parser_context.image_provider.get_pic_url_and_ocr(image, parser_context.get_user())
    except Exception as e:
        logging.error(f"pic_parser Exception occurred: {e}")
        ocr_text = ""

    result_text = ocr_text
    result_json = get_s3_links_for_simple_block_batch([SimpleBlock(type=IMAGE, ocr_text=ocr_text)])
    return result_json, result_text
