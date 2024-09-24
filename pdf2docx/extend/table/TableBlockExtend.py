from __future__ import annotations
import re
from typing import Optional, List

from pydantic import BaseModel, computed_field, PrivateAttr

from pdf2docx.extend.common.BlockExtend import BlockExtend
from pdf2docx.extend.common.RelationConstruct import RelationElement
from pdf2docx.extend.table.RowExtend import RowExtendModel
from pdf2docx.extend.table.RowsExtend import RowsExtend
from pdf2docx.extend.text.TextBlockExtend import TextBlockExtend, BaseBlockModel
from pdf2docx.table.TableBlock import TableBlock


def search_caption(block: TextBlockExtend):
    '''Check if block is table caption.'''
    """for table caption, it should contains word like 表， 图表, table, Table, tab, Tab, 
    with zeor or more space and zero or more number"""
    pattern = r'(表|图表|table|Table|tab|Tab)[\s]*[0-9]+'
    match = re.match(pattern, block.block.text)
    return match[0] if match else None


class TableBlockModel(BaseBlockModel):
    _block: TableBlockExtend = PrivateAttr()
    _order_num: str = PrivateAttr()
    block_type: str = "table"
    page_num: List[int] = []

    def __init__(self, block, order_num:str):
        super().__init__()
        self._block = block
        self._order_num = order_num
        self.page_num = block.page_num

    class Config:
        arbitrary_types_allowed = True

    @computed_field
    @property
    def rows(self) -> List[RowExtendModel]:
        return [RowExtendModel(row, table_order_num=self._order_num) for row in self._block._rows]


class TableBlockExtend(RelationElement, BlockExtend):
    def __init__(self, table_block: TableBlock):
        super().__init__()
        self.block = table_block
        self.caption_block: Optional[TextBlockExtend] = None
        self.table_caption: str = None
        self.refed_blocks: List[TextBlockExtend] = []
        self.bbox = table_block.bbox
        self._rows = RowsExtend(table_block._rows)
        self.next_continuous_table: Optional[TableBlockExtend] = None
        self.prev_continuous_table: Optional[TableBlockExtend] = None
        self.is_catalog = 0

    @property
    def text(self):
        return self.block.text

    @property
    def is_text_block(self):
        return False

    @property
    def is_image_block(self):
        return False

    @property
    def is_table_block(self):
        return True

    def merge(self, table_extend: TableBlockExtend):
        '''Merge two table blocks.'''
        # 记录：发现这里只merge了rows，没有merge text，可能影响输出debug文件
        self._rows.merge_rows(table_extend._rows)

    def table_continous_relation_construct(self, table_extend: TableBlockExtend):
        '''Construct relation between two continuous table blocks.'''
        self.next_continuous_table = table_extend
        table_extend.prev_continuous_table = self

    def relation_construct(self, cur_page, pages):
        self.caption_block, self.table_caption = self.search_table_caption(cur_page)
        self.refed_blocks = self.search_table_reference(pages)

    def search_table_caption(self, cur_page):
        '''Get table caption.'''
        # search table caption in the same page with table block
        blocks = []
        table_block_index = None
        for section in cur_page.sections:
            for column in section:
                for block in column.blocks:
                    if isinstance(block, TextBlockExtend):
                        blocks.append(block)
                    if block == self:
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

    def search_table_reference(self, pages):
        '''Search table reference in all pages.'''
        refed_blocks = []
        if not self.caption_block:
            return refed_blocks
        for page in pages:
            for section in page.sections:
                for column in section:
                    for block in column.blocks:
                        if block.is_text_block:
                            if self.table_caption in block.block.text and block != self.caption_block:
                                refed_blocks.append(block)
                                block.add_ref_table(self)
        return refed_blocks


if __name__ == '__main__':
    pattern = r'(表|图表|table|Table|tab|Tab)[\s]*[0-9]+'
    assert re.match(pattern, '表 1 中国人均GDP')[0] == '表 1'
    assert re.match(pattern, 'Table1 中国人均GDP')[0] == 'Table1'
    assert re.match(pattern, '表2 中国人均GDP')[0] == '表2'
    assert re.match(pattern, '表2. 中国人均GDP')[0] == '表2'
    assert re.match(pattern, '表 2. 中国人均GDP')[0] == '表 2'
    assert re.match(pattern, 'table 2. 中国人均GDP')[0] == 'table 2'
    assert re.match(pattern, 'tab 2. 中国人均GDP')[0] == 'tab 2'
    assert re.match(pattern, '表示 中国人均GDP') is None
