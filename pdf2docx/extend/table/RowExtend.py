from pdf2docx.common.Element import Element
from pdf2docx.extend.table.CellExtend import CellExtend
from pdf2docx.extend.table.CellsExtend import CellsExtend
from pdf2docx.table.Row import Row


class RowExtend(Element):
    def __init__(self, row: Row, row_index):
        super().__init__()
        self._row = row
        self._cells = CellsExtend(row._cells, row_index)
        self.bbox = self._row.bbox
