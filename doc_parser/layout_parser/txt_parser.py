# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu
#    @Create Time   : 2024/11/7
#    @Description   :
#
# ===============================================================

from doc_parser.layout_parser.layout.simple_block import SimpleBlock
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
