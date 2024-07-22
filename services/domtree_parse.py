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
from pdf2docx import Converter
from pdf2docx.dom_tree.domtree import DomTreeModel


def parse(contents: bytes = None):
    converter = Converter(stream=contents)
    dom_tree = converter.dom_tree_parse(
        remove_watermark=True,
        parse_stream_table=False
    )
    return DomTreeModel(dom_tree=dom_tree)
