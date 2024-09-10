from __future__ import annotations

from pdf2docx.common.Collection import BaseCollection
from pdf2docx.extend.page.PageExtend import PageExtend
from pdf2docx.page.Pages import Pages


class PagesExtend(BaseCollection):
    def __init__(self, pages: Pages):
        super().__init__()
        self.pages = pages
        for page in self.pages:
            self.append(PageExtend(page))

    def relation_construct(self):
        for page in self:
            page.relation_construct(self)
        self.table_continous_relation_construct()
        self.paragraph_continous_relation_construct()

    def table_continous_relation_construct(self):
        for page, next_page in zip(self, self[1:]):
            page.table_continous_relation_construct(next_page)

    def paragraph_continous_relation_construct(self):
        for page, next_page in zip(self, self[1:]):
            page.paragraph_continous_relation_construct(next_page)
