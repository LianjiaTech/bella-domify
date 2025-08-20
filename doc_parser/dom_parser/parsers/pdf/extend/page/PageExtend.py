from __future__ import annotations

from doc_parser.dom_parser.parsers.pdf.extend.layout.SectionsExtend import SectionsExtend
from doc_parser.dom_parser.parsers.pdf.page import Page


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
