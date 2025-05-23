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
import logging

import fitz

from services.constants import TEXT, IMAGE
from services.layout_parse_utils import _possible_holder_blocks, mark_holder_by_text_similarity, \
    get_s3_links_for_simple_block_batch, trans_simple_block_list2string
from services.simple_block import SimpleBlock


def trans_block2text(block):
    text = ""
    for line in block["lines"]:
        if (line["dir"][0] == 1.0 or line["dir"][1] == -1.0):
            for span in line["spans"]:
                text += span["text"]
    return text


def layout_parse(file):
    if not file:
        return {}, ""

    page_list = []  # 所有页面list
    try:
        pdf_document = fitz.Document(stream=file)
    except fitz.fitz.FileDataError as e:
        logging.error('layout_parse解析失败。[文件类型]pdf [原因]非pdf类型或损坏的pdf文件 [Exception]:%s', e)
        return ""

    # 遍历每一页
    for page_num in range(len(pdf_document)):
        page_content = []
        page = pdf_document.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        # 发现blocks的顺序不定，有页面下方的页码被排在第一位的情况，故排序
        blocks_sorted = sorted(blocks, key=lambda b: (b['bbox'][1], b['bbox'][0]))
        for block in blocks_sorted:
            if block["type"] == 0:  # 文字块
                text = trans_block2text(block)
                if text and not text.isspace():
                    page_content.append(SimpleBlock(type=TEXT, page_num=page_num, text=text))
            elif block["type"] == 1:  # 图片块
                page_content.append(SimpleBlock(type=IMAGE, page_num=page_num, image_bytes=block.get("image")))
        page_list.append(page_content)

    # 页眉识别
    page_header_blocks = _possible_holder_blocks(page_list, header=True)
    mark_holder_by_text_similarity(page_header_blocks, header=True)
    # 页脚识别
    page_footer_blocks = _possible_holder_blocks(page_list, header=False)
    mark_holder_by_text_similarity(page_footer_blocks, header=False)
    # 过滤无用元素
    filtered_list = []
    for page_item in page_list:
        for simple_block in page_item:
            if not simple_block.is_header and not simple_block.is_footer:
                filtered_list.append(simple_block)

    # SimpleBlock的list批量获取S3链接，并返回目标结构
    result_json = get_s3_links_for_simple_block_batch(filtered_list)
    result_text = trans_simple_block_list2string(result_json)
    return result_json, result_text


def get_page_count(file):
    pdf_document = fitz.Document(stream=file)
    return len(pdf_document)


if __name__ == "__main__":

    file_name = 'demo_table.pdf'

    # 读取本地文件
    try:
        with open(file_name, 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        print(f"读取文件失败: {e}")

    print(json.dumps(layout_parse(buf_data), ensure_ascii=False))
