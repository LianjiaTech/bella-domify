# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/7/16
#    @Description   : 
#
# ===============================================================
from services import layout_parse_pptx, layout_parse_docx, layout_parse_pdf


def parse(file_name: str = None, file: bytes = None):
    # 检查文件名是否包含后缀
    if '.' not in file_name:
        raise ValueError("异常：文件名没有包含后缀")
    # 获取文件后缀
    file_extension = file_name.split('.')[-1].lower()
    # 根据后缀判断文件类型
    if file_extension == 'pptx':
        return layout_parse_pptx.layout_parse(file)
    elif file_extension == 'pdf':
        return layout_parse_pdf.layout_parse(file)
    elif file_extension == 'docx':
        return layout_parse_docx.layout_parse(file)
    else:
        raise ValueError("异常：不支持的文件类型")
