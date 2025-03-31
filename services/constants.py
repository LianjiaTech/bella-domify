# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/7/17
#    @Description   : 
#
# ===============================================================

from enum import Enum


IMAGE = "image"
TEXT = "text"
TABLE = "table"

OPENAI_API_KEY = "8d7b1d17-1478-408c-9180-795b148dc6b2"


class ParseType(Enum):
    All = "all"
    LAYOUT = "layout"
    DOMTREE = "domtree"
    MARKDOWN = "markdown"


GROUP_ID_LONG_TASK = "document_parser_long_task_group"
GROUP_ID_SHORT_TASK = "document_parser_short_task_group"
GROUP_ID_IMAGE_TASK = "document_parser_image_task_group"
