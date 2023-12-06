from __future__ import annotations
from pdf2docx.extend.layout.SectionsExtend import SectionsExtend
from pdf2docx.page import Page


class PageExtend:
    def __init__(self, page: Page):
        self.page = page
        self.sections = SectionsExtend(self.page.sections)

    def relation_construct(self, pages):
        self.sections.relation_construct(self, pages)
