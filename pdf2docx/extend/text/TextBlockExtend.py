from __future__ import annotations

from typing import Union

from pydantic import BaseModel, computed_field

from pdf2docx.extend.common.BlockExtend import BlockExtend
from pdf2docx.extend.common.RelationConstruct import RelationElement
from pdf2docx.extend.text.LinesExtend import LinesExtend
from pdf2docx.text.TextBlock import TextBlock
import base64


class TextBlockModel(BaseModel):
    _block: TextBlockExtend

    def __init__(self, block):
        super().__init__()
        self._block = block

    class Config:
        arbitrary_types_allowed = True

    @computed_field
    @property
    def text(self) -> Union[str, None]:
        if self._block.is_image_block:
            return None
        return self._block.block.text

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
        if self.block_type == "image":
            image_span = self._block.lines.image_spans[0]
            bytes = image_span.image_span.image
            return base64.b64encode(bytes).decode('utf-8')
        return None




class TextBlockExtend(RelationElement, BlockExtend):
    def __init__(self, text_block: TextBlock):
        super().__init__()
        self.block = text_block
        self.lines = LinesExtend(text_block.lines)
        self.ref_tables = []
        self.ref_images = []
        self.bbox = text_block.bbox

    @property
    def is_text_block(self):
        return not self.is_image_block

    @property
    def is_image_block(self):
        return self.block.lines.image_spans

    @property
    def is_table_block(self):
        return False

    def add_ref_table(self, ref_table):
        self.ref_tables.append(ref_table)

    def add_ref_image(self, ref_image):
        self.ref_images.append(ref_image)

    def relation_construct(self, cur_page, pages):
        for line in self.lines:
            line.relation_construct(cur_page, pages)
