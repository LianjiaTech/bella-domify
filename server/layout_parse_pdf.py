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
import json
import fitz

from server import utils
from server.constants import TEXT, TABLE


def trans_block2text(block):
    text = ""
    for line in block["lines"]:
        for span in line["spans"]:
            text += span["text"]
    return text


def layout_parse(file):
    layouts = []

    pdf_document = fitz.Document(stream=file)

    # 遍历每一页
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] == 0:  # 文字块
                layouts.append(dict(text=trans_block2text(block), type=TEXT))
            elif block["type"] == 1:  # 图片块
                layouts.append(utils.build_image_item(block.get("image")))
            elif block["type"] == 2:  # 表格块（假设表格是用线条绘制的）
                layouts.append((TABLE, block["lines"]))

    return layouts


if __name__ == "__main__":

    file_name = 'demo_table.pdf'

    # 读取本地文件
    try:
        with open(file_name, 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        print(f"读取文件失败: {e}")

    print(json.dumps(layout_parse(buf_data), ensure_ascii=False))
