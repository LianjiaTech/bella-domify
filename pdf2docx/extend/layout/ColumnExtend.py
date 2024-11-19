from pdf2docx.extend.common.RelationConstruct import RelationElement
from pdf2docx.extend.table.TableBlockExtend import TableBlockExtend
from pdf2docx.extend.text.TextBlockExtend import TextBlockExtend
from pdf2docx.layout.Column import Column
from pdf2docx.table.TableBlock import TableBlock
from pdf2docx.text.TextBlock import TextBlock


class ColumnExtend(RelationElement):
    def __init__(self, column: Column):
        self.column = column
        self.blocks = []
        for block in self.column.blocks:
            if isinstance(block, TextBlock):
                self.blocks.append(TextBlockExtend(block))
            elif isinstance(block, TableBlock):
                self.blocks.append(TableBlockExtend(block))

    def relation_construct(self, cur_page, pages):
        for block in self.blocks:
            block.relation_construct(cur_page, pages)

    def table_continous_relation_construct(self, next_col):
        cur_blocks = [block for block in self.blocks
                      if not block.block.is_header and not block.block.is_footer]
        next_blocks = [block for block in next_col.blocks
                       if not block.block.is_header and not block.block.is_footer]
        if cur_blocks and next_blocks and cur_blocks[-1].is_table_block and next_blocks[0].is_table_block:
            cur_blocks[-1].table_continous_relation_construct(next_blocks[0])

    def paragraph_continous_relation_construct(self, next_col):
        cur_blocks = [block for block in self.blocks
                      if not block.block.is_header and not block.block.is_footer]
        next_blocks = [block for block in next_col.blocks
                       if not block.block.is_header and not block.block.is_footer]
        if cur_blocks and next_blocks and cur_blocks[-1].is_text_block and next_blocks[0].is_text_block:
            cur_blocks[-1].paragraph_continous_relation_construct(next_blocks[0])
