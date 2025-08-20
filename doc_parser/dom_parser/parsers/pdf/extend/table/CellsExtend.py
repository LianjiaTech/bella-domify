from doc_parser.dom_parser.parsers.pdf.common.Collection import ElementCollection
from doc_parser.dom_parser.parsers.pdf.extend.table.CellExtend import CellExtend
from doc_parser.dom_parser.parsers.pdf.table.Cells import Cells


class CellsExtend(ElementCollection):
    def __init__(self, cells: Cells, row_index):
        super().__init__()
        self._cells = cells
        for col_index, cell in enumerate(self._cells):
            self.append(CellExtend(cell, row_index, col_index))
