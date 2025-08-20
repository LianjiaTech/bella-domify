from __future__ import annotations

from pydantic import BaseModel, PrivateAttr, computed_field

from doc_parser.dom_parser.parsers.pdf.common.Element import Element
from doc_parser.dom_parser.parsers.pdf.table import Cell


class CellExtendModel(BaseModel):
    _cell: CellExtend = PrivateAttr()
    _talbe_order_num: str = PrivateAttr()

    def __init__(self, cell, table_order_num: str):
        super().__init__()
        self._cell = cell
        self._talbe_order_num = table_order_num

    @computed_field
    @property
    def order_num(self) -> str:
        return self._talbe_order_num + '.' + "-".join([str(self.start_row), str(self.end_row), str(self.start_col), str(self.end_col)])

    @computed_field
    @property
    def text(self) -> str:
        return self._cell.text

    @computed_field
    @property
    def start_row(self) -> int:
        return self._cell.start_row

    @computed_field
    @property
    def end_row(self) -> int:
        return self._cell.end_row

    @computed_field
    @property
    def start_col(self) -> int:
        return self._cell.start_col

    @computed_field
    @property
    def end_col(self) -> int:
        return self._cell.end_col


class CellExtend(Element):
    def __init__(self, cell: Cell, row_index, col_index):
        super().__init__()
        self._cell = cell
        self.row_index = row_index
        self.col_index = col_index
        self.bbox = self._cell.bbox

    @property
    def start_row(self):
        return self.row_index + 1

    @property
    def end_row(self):
        return self.row_index + self._cell.merged_cells[0]

    @property
    def start_col(self):
        return self.col_index + 1

    @property
    def end_col(self):
        return self.col_index + self._cell.merged_cells[1]

    @property
    def text(self):
        return self._cell.text

    def __str__(self):
        return f"CellExtend(row:{self.start_row}-{self.end_row}, col:{self.start_col}-{self.end_col}, {self.text})"

    def __repr__(self):
        return self.__str__()
