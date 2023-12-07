from pdf2docx.common.Collection import ElementCollection
from pdf2docx.extend.table.RowExtend import RowExtend
from pdf2docx.table.Rows import Rows


class RowsExtend(ElementCollection):
    def __init__(self, rows: Rows):
        super().__init__()
        self._rows = rows
        for row_index, row in enumerate(self._rows):
            self.append(RowExtend(row, row_index))
