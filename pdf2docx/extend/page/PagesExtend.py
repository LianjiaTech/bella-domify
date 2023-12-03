import re
from collections import Counter
from typing import List, Optional

from pdf2docx.common.Block import Block
from pdf2docx.page.Pages import Pages


def _extract_block_text(block):
    if not block:
        return None
    if block.is_text_block:
        return block.text
    elif block.is_table_block:
        return "".join(["".join([cell for cell in row if cell]) for row in block.text if row])
    elif block.is_image_block:
        return "image"
    else:
        return None


def _extract_text(blocks: List[Optional[Block]]):
    if not blocks:
        return
    return [_extract_block_text(block).strip() if block else None for block in blocks]


def remove_number(text):
    # 在页眉，页脚，经常出现次序编号，首先将这些编号去掉,通过剩余文本的相似度，分析是否是页眉页脚
    chinese_number = r'[(一|二|三|四|五|六|七|八|九|十)万]?[(一|二|三|四|五|六|七|八|九)千]?[(一|二|三|四|五|六|七|八|九)百]?[(一|二|三|四|五|六|七|八|九)十]?[(一|二|三|四|五|六|七|八|九)]?'
    # 使用正则表达式，替换符合pattern中的字符为空
    text = re.sub(chinese_number, '', text)
    # 替换所有的数字为空
    text = re.sub(r'\d+', '', text)
    return text.strip()


class PagesExtend:
    def __init__(self, pages: Pages):
        self.pages = pages

    def mark_page_header(self):
        """
        mark page header
        in page header, most text are common except for some numbers represent page number, chatpter number
        """
        header_blocks = self._possible_header_blocks()
        for column_blocks in header_blocks:
            if self.mark_by_text_similarity(column_blocks, header=True):
                continue
        return None

    def _possible_header_blocks(self):
        # for each page, we collect the first blocks in each column in the first section
        page_header_blocks = []  # List[List[Optional[Block]]], each element is a list of blocks in a column
        last_page_columns = None
        for page in self.pages:
            if not page.finalized:
                continue
            if not page.sections:
                continue
            if last_page_columns and len(page.sections[0]) != last_page_columns:
                # if blocks num is not same, we can't mark it as header
                return []
            else:
                last_page_columns = len(page.sections[0])

            for i, column in enumerate(page.sections[0]):
                if len(page_header_blocks) <= i:
                    page_header_blocks.append([])
                page_header_blocks[i].append(column.blocks[0] if column.blocks else None)

        return page_header_blocks

    def _possible_footer_blocks(self):
        # for each page, we collect the last blocks in each column in the last section
        page_footer_blocks = []  # List[List[Optional[Block]]], each element is a list of blocks in a column
        last_page_columns = None
        for page in self.pages:
            if not page.finalized:
                continue
            if not page.sections:
                continue
            if last_page_columns and len(page.sections[-1]) != last_page_columns:
                # if blocks num is not same, we can't mark it as header
                return []
            else:
                last_page_columns = len(page.sections[-1])

            for i, column in enumerate(page.sections[-1]):
                if len(page_footer_blocks) <= i:
                    page_footer_blocks.append([])
                page_footer_blocks[i].append(column.blocks[-1] if column.blocks else None)

        return page_footer_blocks

    def mark_page_footer(self):
        """mark page footer"""
        footer_blocks = self._possible_footer_blocks()
        for column_blocks in footer_blocks:
            if self.mark_by_text_similarity(column_blocks, header=False):
                continue
        return None

    def mark_by_text_similarity(self, blocks: List[Optional[Block]], *, header: bool):
        """
        in most case, text in page header or footer is same, except for some numbers represent page number, chatpter number,
        we can use the similarity of text to judge whether block is header or footer
        """
        text_list = _extract_text(blocks)
        text_list = [remove_number(text) if text else None for text in text_list]
        text_counter = Counter(text_list)
        frequency, most_common_text = text_counter.most_common(1)[0][1], text_counter.most_common(1)[0][0]
        found = False
        if frequency / len(text_list) > 0.5:
            found = True
        if found:
            for block in blocks:
                if remove_number(_extract_block_text(block)) == most_common_text:
                    block.mark_header() if header else block.mark_footer()
                    if header:
                        block.mark_header()

        return found
