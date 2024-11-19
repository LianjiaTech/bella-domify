from pdf2docx.common.Collection import BaseCollection
from pdf2docx.extend.common.RelationConstruct import RelationElement
from pdf2docx.extend.layout.SectionExtend import SectionExtend
from pdf2docx.layout.Sections import Sections


class SectionsExtend(BaseCollection, RelationElement):
    def __init__(self, sections: Sections):
        super().__init__()
        self.sections = sections
        for section in self.sections:
            self.append(SectionExtend(section))

    def relation_construct(self, cur_page, pages):
        for section in self:
            section.relation_construct(cur_page, pages)
        self.table_continous_relation_construct()
        self.paragraph_continous_relation_construct()

    def table_continous_relation_construct(self):
        for cur_section, next_section in zip(self, self[1:]):
            cur_section.table_continous_relation_construct(next_section)

    def paragraph_continous_relation_construct(self):
        for cur_section, next_section in zip(self, self[1:]):
            cur_section.paragraph_continous_relation_construct(next_section)
