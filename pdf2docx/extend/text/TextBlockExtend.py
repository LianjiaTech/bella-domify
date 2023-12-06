from pdf2docx.extend.text.LinesExtend import LinesExtend
from pdf2docx.page import Page
from pdf2docx.page.Pages import Pages
from pdf2docx.text.TextBlock import TextBlock


class TextBlockExtend:
    def __init__(self, text_block: TextBlock, page_of_text_block: Page, pages: Pages):
        self.text_block = text_block
        self.lines = LinesExtend(text_block.lines, page_of_text_block, pages)
