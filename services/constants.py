# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu
#    @Create Time   : 2024/7/17
#    @Description   : 
#
# ===============================================================

from enum import Enum
import os


IMAGE = "image"
TEXT = "text"
TABLE = "table"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class ParseType(Enum):
    All = "all"
    LAYOUT = "layout"
    DOMTREE = "domtree"
    MARKDOWN = "markdown"


GROUP_ID_LONG_TASK = "document_parser_long_task_group"
GROUP_ID_SHORT_TASK = "document_parser_short_task_group"
GROUP_ID_IMAGE_TASK = "document_parser_image_task_group"
GROUP_ID_DOC_TASK = "document_parser_doc_task_group"
