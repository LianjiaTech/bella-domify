from doc_parser.dom_parser.parsers.pdf.common.Collection import BaseCollection
from doc_parser.dom_parser.parsers.pdf.extend.common.RelationConstruct import RelationElement
from doc_parser.dom_parser.parsers.pdf.extend.layout.ColumnExtend import ColumnExtend
from doc_parser.dom_parser.parsers.pdf.layout.Section import Section


class SectionExtend(BaseCollection, RelationElement):
    def __init__(self, section: Section):
        super().__init__()
        self.section = section
        for column in self.section:
            self.append(ColumnExtend(column))

    def relation_construct(self, cur_page, pages):
        for column in self:
            column.relation_construct(cur_page, pages)
        self.cols_table_continous_relation_construct()
        self.cols_paragraph_continous_relation_construct()

    def table_continous_relation_construct(self, next_section):
        cur_blocks = [block for column in self for block in column.blocks
                      if not block.block.is_header and not block.block.is_footer]
        next_blocks = [block for column in next_section for block in column.blocks
                       if not block.block.is_header and not block.block.is_footer]
        if cur_blocks and next_blocks and cur_blocks[-1].is_table_block and next_blocks[0].is_table_block:
            cur_blocks[-1].table_continous_relation_construct(next_blocks[0])

    def paragraph_continous_relation_construct(self, next_section):
        cur_blocks = [block for column in self for block in column.blocks
                      if not block.block.is_header and not block.block.is_footer]
        next_blocks = [block for column in next_section for block in column.blocks
                       if not block.block.is_header and not block.block.is_footer]
        if cur_blocks and next_blocks and cur_blocks[-1].is_text_block and next_blocks[0].is_text_block:
            cur_blocks[-1].paragraph_continous_relation_construct(next_blocks[0])

    def cols_table_continous_relation_construct(self):
        for cur_col, next_col in zip(self, self[1:]):
            cur_col.table_continous_relation_construct(next_col)

    def cols_paragraph_continous_relation_construct(self):
        for cur_col, next_col in zip(self, self[1:]):
            cur_col.paragraph_continous_relation_construct(next_col)