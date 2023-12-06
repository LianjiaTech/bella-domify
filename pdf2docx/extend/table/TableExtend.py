import re

from pdf2docx.page import Page
from pdf2docx.page.Pages import Pages
from pdf2docx.table.TableBlock import TableBlock
from pdf2docx.text.TextBlock import TextBlock


def search_caption(block: TextBlock):
    '''Check if block is table caption.'''
    """for table caption, it should contains word like 表， 图表, table, Table, tab, Tab, 
    with zeor or more space and zero or more number"""
    pattern = r'(表|图表|table|Table|tab|Tab)[\s]*[0-9]+'
    match = re.match(pattern, block.text)
    return match[0] if match else None


class TableExtend:
    def __init__(self, table_block: TableBlock, page_of_table: Page, all_pages: Pages):
        self.table_block = table_block
        self.page_of_table = page_of_table  # table block is in which page
        self.all_pages = all_pages
        self.caption_block, self.table_caption = self.search_table_caption()
        self.ref_blocks = self.search_table_reference()

    def search_table_caption(self):
        '''Get table caption.'''
        # search table caption in the same page with table block
        blocks = []
        table_block_index = None
        for section in self.page_of_table.sections:
            for column in section:
                for block in column.blocks:
                    if block.is_text_block:
                        blocks.append(block)
                    if block == self.table_block:
                        blocks.append(block)
                        table_block_index = len(blocks) - 1
        # serach table caption from center to two sides
        caption_block, table_caption = None, None
        # search 2 blocks before and after table block
        for i in range(1, 3):
            prev_block, next_block = None, None
            if table_block_index - i > 0:
                prev_block = blocks[table_block_index - i]
            if table_block_index + i < len(blocks):
                next_block = blocks[table_block_index + i]
            if not prev_block and not next_block:
                break
            if prev_block and search_caption(prev_block):
                caption_block = prev_block
                table_caption = search_caption(prev_block)
                break
            if next_block and search_caption(next_block):
                caption_block = next_block
                table_caption = search_caption(next_block)
                break
        return caption_block, table_caption

    def search_table_reference(self):
        '''Search table reference in all pages.'''
        ref_blocks = []
        if not self.caption_block:
            return ref_blocks
        for page in self.all_pages:
            for section in page.sections:
                for column in section:
                    for block in column.blocks:
                        if block.is_text_block:
                            if self.table_caption in block.text and block != self.caption_block:
                                ref_blocks.append(block)
        return ref_blocks


if __name__ == '__main__':
    pattern = r'(表|图表|table|Table|tab|Tab)[\s]*[0-9]+'
    assert re.match(pattern, '表 1 中国人均GDP')[0] == '表 1'
    assert re.match(pattern, 'Table1 中国人均GDP')[0] == 'Table1'
    assert re.match(pattern, '表2 中国人均GDP')[0] == '表2'
    assert re.match(pattern, '表2. 中国人均GDP')[0] == '表2'
    assert re.match(pattern, '表 2. 中国人均GDP')[0] == '表 2'
    assert re.match(pattern, 'table 2. 中国人均GDP')[0] == 'table 2'
    assert re.match(pattern, 'tab 2. 中国人均GDP')[0] == 'tab 2'
    assert re.match(pattern, '表示 中国人均GDP') == None
