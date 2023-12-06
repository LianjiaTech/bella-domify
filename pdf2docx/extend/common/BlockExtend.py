from pdf2docx.common.Element import Element


class BlockExtend(Element):

    @property
    def is_image_block(self):
        raise NotImplementedError

    @property
    def is_text_block(self):
        raise NotImplementedError

    @property
    def is_table_block(self):
        raise NotImplementedError
