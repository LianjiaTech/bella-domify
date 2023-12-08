from pydantic import BaseModel, PrivateAttr, computed_field

from pdf2docx.common.Element import Element
from pdf2docx.extend.table.CellExtend import CellExtend, CellExtendModel
from pdf2docx.extend.table.CellsExtend import CellsExtend
from pdf2docx.table.Row import Row


class RowExtend(Element):
    def __init__(self, row: Row, row_index):
        super().__init__()
        self._row = row
        self._cells = CellsExtend(row._cells, row_index)
        self.bbox = self._row.bbox


class RowExtendModel(BaseModel):
    _row: RowExtend = PrivateAttr()

    def __init__(self, row):
        super().__init__()
        self._row = row

    class Config:
        arbitrary_types_allowed = True

    @computed_field
    @property
    def cells(self) -> list[CellExtendModel]:
        return [CellExtendModel(cell=cell) for cell in self._row._cells]