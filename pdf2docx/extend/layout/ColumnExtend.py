from pdf2docx.extend.table.TableBlockExtend import TableBlockExtend
from pdf2docx.extend.text.TextBlockExtend import TextBlockExtend
from pdf2docx.layout.Column import Column
from pdf2docx.page import Page
from pdf2docx.page.Pages import Pages
from pdf2docx.table.TableBlock import TableBlock
from pdf2docx.text.TextBlock import TextBlock


class ColumnExtend:
    def __init__(self, column: Column, page_of_column: Page, pages: Pages):
        self.column = column
        self.blocks = []
        for block in self.column.blocks:
            if isinstance(block, TextBlock):
                self.blocks.append(TextBlockExtend(block, page_of_column, pages))
            elif isinstance(block, TableBlock):
                self.blocks.append(TableBlockExtend(block, page_of_column, pages))


