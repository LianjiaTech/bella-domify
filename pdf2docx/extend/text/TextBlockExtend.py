from __future__ import annotations

from typing import List
from typing import Union, Optional

from pydantic import BaseModel, computed_field

from pdf2docx.extend.common.BlockExtend import BlockExtend
from pdf2docx.extend.common.RelationConstruct import RelationElement
from pdf2docx.extend.text.LinesExtend import LinesExtend
from pdf2docx.text.TextBlock import TextBlock
from utils.general_util import get_pic_url_and_ocr


class BaseBlockModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    @computed_field
    @property
    def layout_type(self) -> str:
        return self._block.layout_type

    @computed_field
    @property
    def bbox(self) -> list:
        return list(self._block.bbox)


class TextBlockModel(BaseBlockModel):
    _block: TextBlockExtend

    def __init__(self, block):
        super().__init__()
        self._block = block

    @computed_field
    @property
    def metadata(self) -> Optional[dict]:
        return self._block.metadata

    @computed_field
    @property
    def text(self) -> Union[str, None]:
        if self._block.is_image_block:
            return None
        return self._block.text

    @computed_field
    @property
    def page_num(self) -> List[int]:
        return self._block.page_num

    @computed_field
    @property
    def block_type(self) -> str:
        if self._block.is_image_block:
            return "image"
        else:
            return "text"

    @computed_field
    @property
    def image_s3_link(self) -> Union[str, None]:
        return self._block.image_s3_link

    @computed_field
    @property
    def image_ocr_result(self) -> Union[str, None]:
        return self._block.image_ocr_result


class TextBlockExtend(RelationElement, BlockExtend):
    def __init__(self, text_block: TextBlock, metadata: Optional[dict] = None):
        super().__init__()
        self.block = text_block
        self.lines = LinesExtend(text_block.lines)
        self.ref_tables = []
        self.ref_images = []
        self.bbox = text_block.bbox
        self.next_continuous_paragraph: Optional[TextBlockExtend] = None
        self.prev_continuous_paragraph: Optional[TextBlockExtend] = None
        self.metadata = metadata
        self.image_s3_link = None
        self.image_ocr_result = None
        self.page_num = 0  # -1:无页码
        self.is_table_name = 0
        self.is_figure_name = 0
        self.is_title = text_block.is_title
        self.is_catalog = self.get_is_catalog()

    @property
    def text(self):
        return "".join([line.text for line in self.lines])

    @property
    def raw_text(self):
        return "".join([line.raw_text for line in self.lines])

    @property
    def is_text_block(self):
        return not self.is_image_block

    @property
    def is_image_block(self):
        return self.block.lines.image_spans

    @property
    def is_table_block(self):
        return False

    @computed_field
    @property
    def layout_type(self) -> str:
        # 所属部分 优先级最高
        if self.is_catalog:
            return "Catalog"
        # 元素类型
        elif self.is_image_block:
            return "Figure"
        elif self.is_table_block:
            return "Table"
        elif self.is_table_name:
            return "TableName"
        elif self.is_figure_name:
            return "FigureName"
        elif self.is_title:
            return "Title"
        elif self.block.list_type():
            return "List"
        else:
            return "Text"
    
    def get_is_catalog(self):
        return any([line.is_catalog for line in self.lines])

    def image_handler(self, user):
        if self.is_image_block:
            image_span = self.lines.image_spans[0]
            image_bytes = image_span.image_span.image
            # review-todo：这里要重构，最好module内自闭环
            image_s3_url, ocr_text = get_pic_url_and_ocr(image_bytes, user)
            self.image_s3_link = image_s3_url
            self.image_ocr_result = ocr_text

    def add_ref_table(self, ref_table):
        self.ref_tables.append(ref_table)

    def add_ref_image(self, ref_image):
        self.ref_images.append(ref_image)

    def relation_construct(self, cur_page, pages):
        for line in self.lines:
            line.relation_construct(cur_page, pages)

    def paragraph_continous_relation_construct(self, next_paragraph: TextBlockExtend):
        '''Construct relation between two continuous paragraph blocks.'''
        # 如果当前段落最后一行不是段落结束句, 并且下一段落的第一句不是段落句起始句, 则两段落连续
        if not self.block.last_line_end_of_paragraph and not next_paragraph.block.first_line_start_of_paragraph:
            self.next_continuous_paragraph = next_paragraph
            next_paragraph.prev_continuous_paragraph = self

    def merge(self, next_paragraph: TextBlockExtend):
        '''Merge two paragraph blocks.'''
        self.lines.merge(next_paragraph.lines)
