from pdf2docx.common.Element import Element


class BlockExtend(Element):
    def __init__(self):
        super().__init__()
        self.is_catalog = 0
        self.page_num = 0  # -1:无页码
        self.is_title = 0

    @property
    def is_image_block(self):
        raise NotImplementedError

    @property
    def is_text_block(self):
        raise NotImplementedError

    @property
    def is_table_block(self):
        raise NotImplementedError
