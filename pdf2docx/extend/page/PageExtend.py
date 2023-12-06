from pdf2docx.extend.layout.SectionsExtend import SectionsExtend
from pdf2docx.page import Page
from pdf2docx.page.Pages import Pages


class PageExtend:
    def __init__(self, page: Page, pages: Pages):
        self.page = page
        self.sections = SectionsExtend(self.page.sections, page, pages)