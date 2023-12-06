from pdf2docx.common.Collection import BaseCollection
from pdf2docx.extend.layout.ColumnExtend import ColumnExtend
from pdf2docx.layout.Section import Section
from pdf2docx.page import Page
from pdf2docx.page.Pages import Pages


class SectionExtend(BaseCollection):
    def __init__(self, section: Section, page_of_section: Page, pages: Pages):
        super().__init__()
        self.section = section
        for column in self.section:
            self.append(ColumnExtend(column, page_of_section, pages))
