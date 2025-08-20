from __future__ import annotations

from doc_parser.dom_parser.parsers.pdf.common.Collection import ElementCollection
from doc_parser.dom_parser.parsers.pdf.extend.table.RowExtend import RowExtend
from doc_parser.dom_parser.parsers.pdf.table import Rows


class RowsExtend(ElementCollection):
    def __init__(self, rows: Rows):
        super().__init__()
        self._rows = rows
        for row_index, row in enumerate(self._rows):
            self.append(RowExtend(row, row_index))

    def merge_rows(self, rows: RowsExtend):
        start_row_index = len(self)
        for i, row in enumerate(rows):
            self.append(RowExtend(row._row, start_row_index+i))
