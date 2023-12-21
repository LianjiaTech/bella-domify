from __future__ import annotations
from pdf2docx.extend.layout.SectionsExtend import SectionsExtend
from pdf2docx.extend.table.TableBlockExtend import TableBlockExtend
from pdf2docx.page import Page


class PageExtend:
    def __init__(self, page: Page):
        self.page = page
        self.sections = SectionsExtend(self.page.sections)

    def relation_construct(self, pages):
        self.sections.relation_construct(self, pages)

    def table_continous_relation_construct(self, next_page):
        blocks = [block for section in self.sections for column in section for block in column.blocks
                  if not block.block.is_header and not block.block.is_footer]
        next_page_blocks = [block for section in next_page.sections for column in section for block in column.blocks
                            if not block.block.is_header and not block.block.is_footer]
        if blocks and next_page_blocks and blocks[-1].is_table_block and next_page_blocks[0].is_table_block:
            blocks[-1].table_continous_relation_construct(next_page_blocks[0])

    def paragraph_continous_relation_construct(self, next_page):
        blocks = [block for section in self.sections for column in section for block in column.blocks
                  if not block.block.is_header and not block.block.is_footer]
        next_page_blocks = [block for section in next_page.sections for column in section for block in column.blocks
                            if not block.block.is_header and not block.block.is_footer]
        if blocks and next_page_blocks and blocks[-1].is_text_block and next_page_blocks[0].is_text_block:
            blocks[-1].paragraph_continous_relation_construct(next_page_blocks[0])

    def paragraph_continous_cross_column_relation_construct(self):
        for section in self.sections:
            if len(section) <= 1:
                continue
            for cur_col, next_col in zip(section, section[1:]):
                cur_col_block = [block for block in cur_col.blocks if
                                 not block.block.is_header and not block.block.is_footer]
                next_col_block = [block for block in next_col.blocks if
                                  not block.block.is_header and not block.block.is_footer]
                if (cur_col_block and next_col_block and cur_col_block[-1].is_text_block
                        and next_col_block[0].is_text_block):
                    cur_col_block[-1].paragraph_continous_relation_construct(next_col_block[0])
