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

OPENAI_API_KEY = "qaekDD2hBoZE4ArZZlOQ9fYTQ74Qc8mq"


class ParseType(Enum):
    All = "all"
    LAYOUT = "layout"
    DOMTREE = "domtree"
    MARKDOWN = "markdown"
