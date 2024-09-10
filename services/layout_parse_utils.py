# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/7/31
#    @Description   : 
#
# ===============================================================
import concurrent.futures
import re
from collections import Counter

from services.constants import TEXT, IMAGE


def remove_number(text):
    if text is None:
        return None
    # 在页眉，页脚，经常出现次序编号，首先将这些编号去掉,通过剩余文本的相似度，分析是否是页眉页脚
    chinese_number = r'[(一|二|三|四|五|六|七|八|九|十)万]?[(一|二|三|四|五|六|七|八|九)千]?[(一|二|三|四|五|六|七|八|九)百]?[(一|二|三|四|五|六|七|八|九)十]?[(一|二|三|四|五|六|七|八|九)]?'
    # 使用正则表达式，替换符合pattern中的字符为空
    text = re.sub(chinese_number, '', text)
    # 替换所有的数字为空
    text = re.sub(r'\d+', '', text)
    return text.strip()


def _possible_holder_blocks(page_list, header: bool = True):
    page_header_blocks = []
    for page_item in page_list:
        if header:
            page_header_blocks.append(page_item[0])
        else:
            page_header_blocks.append(page_item[-1])
    return page_header_blocks


def mark_holder_by_text_similarity(page_holder_blocks, header: bool = True):
    """
    本方法通过每页第一个元素的相似度，去除页眉
    """
    # 抽象元素：第一个元素若是图片，则抽象为IMAGE字段；若是文字，则抽象为去除数字的正则式；
    raw_text_list = []
    for item in page_holder_blocks:
        if item.type == TEXT:
            raw_text_list.append(item.text)
        elif item.type == IMAGE:
            raw_text_list.append(IMAGE)
    text_list = [remove_number(text) if text else None for text in raw_text_list]

    # 计算频率：若有元素出现频率过半，则识别为页眉
    text_counter = Counter(text_list)
    frequency, most_common_text = text_counter.most_common(1)[0][1], text_counter.most_common(1)[0][0]
    if most_common_text is None:
        return False
    found = False
    if frequency / len(text_list) > 0.5 and frequency > 1:
        found = True
    if found:
        # 若页眉为图像，则只处理每页第一元素为图像
        if most_common_text == IMAGE:
            for item in page_holder_blocks:
                if item.type == IMAGE:
                    item.mark_holder(header)

        # 若页眉为文字，则用文字匹配处理
        else:
            for item in page_holder_blocks:
                if remove_number(item.text) == most_common_text:
                    item.mark_holder(header)
    return found


def get_s3_links_for_simple_block_batch(simple_block_list):
    """
    SimpleBlock的list批量获取S3链接，并返回目标结构
    """
    result = []
    # 多进程获取S3链接
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(lambda simple_block: simple_block.generate_s3_url(), simple_block_list)

    for simple_block in simple_block_list:
        result.append(simple_block.get_result())
    return result