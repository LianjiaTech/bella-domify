from pdf2docx.common.Collection import BaseCollection
from pdf2docx.extend.layout.SectionExtend import SectionExtend
from pdf2docx.layout.Sections import Sections
from pdf2docx.page import Page
from pdf2docx.page.Pages import Pages


class SectionsExtend(BaseCollection):
    def __init__(self, sections: Sections, page_of_sections: Page, pages: Pages):
        super().__init__()
        self.sections = sections
        for section in self.sections:
            self.append(SectionExtend(section, page_of_sections, pages))
