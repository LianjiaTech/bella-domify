from pdf2docx.extend.common.RelationConstruct import RelationElement
from pdf2docx.extend.text.LinesExtend import LinesExtend
from pdf2docx.text.TextBlock import TextBlock


class TextBlockExtend(RelationElement):
    def __init__(self, text_block: TextBlock):
        self.block = text_block
        self.lines = LinesExtend(text_block.lines)
        self.ref_tables = []
        self.ref_images = []

    def add_ref_table(self, ref_table):
        self.ref_tables.append(ref_table)

    def add_ref_image(self, ref_image):
        self.ref_images.append(ref_image)

    def relation_construct(self, cur_page, pages):
        for line in self.lines:
            line.relation_construct(cur_page, pages)