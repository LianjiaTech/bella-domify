from __future__ import annotations

from typing import Union, Optional
from typing import List

from pydantic import BaseModel, computed_field

from pdf2docx.extend.common.BlockExtend import BlockExtend
from pdf2docx.extend.common.RelationConstruct import RelationElement
from pdf2docx.extend.text.LinesExtend import LinesExtend
from pdf2docx.text.TextBlock import TextBlock
from server.task_executor import s3


class TextBlockModel(BaseModel):
    _block: TextBlockExtend

    def __init__(self, block):
        super().__init__()
        self._block = block

    class Config:
        arbitrary_types_allowed = True

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
    def image_base64_str(self) -> Union[str, None]:
        # if self.block_type == "image":
        #     image_span = self._block.lines.image_spans[0]
        #     bytes = image_span.image_span.image
        #     return base64.b64encode(bytes).decode('utf-8')
        return None


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

    def get_image_s3_link(self):
        if self.is_image_block:
            image_span = self.lines.image_spans[0]
            bytes = image_span.image_span.image
            file_key = s3.upload_file(stream=bytes)
            self.image_s3_link = s3.get_file_url(file_key)

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
