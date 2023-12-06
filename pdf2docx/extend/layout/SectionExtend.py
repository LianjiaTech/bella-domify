from pdf2docx.common.Collection import BaseCollection
from pdf2docx.extend.common.RelationConstruct import RelationElement
from pdf2docx.extend.layout.ColumnExtend import ColumnExtend
from pdf2docx.layout.Section import Section


class SectionExtend(BaseCollection, RelationElement):
    def __init__(self, section: Section):
        super().__init__()
        self.section = section
        for column in self.section:
            self.append(ColumnExtend(column))

    def relation_construct(self, cur_page, pages):
        for column in self:
            column.relation_construct(cur_page, pages)