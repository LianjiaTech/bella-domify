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

