from pdf2docx.common.Collection import ElementCollection
from pdf2docx.extend.table.CellExtend import CellExtend
from pdf2docx.table.Cells import Cells


class CellsExtend(ElementCollection):
    def __init__(self, cells: Cells, row_index):
        super().__init__()
        self._cells = cells
        for col_index, cell in enumerate(self._cells):
            self.append(CellExtend(cell, row_index, col_index))