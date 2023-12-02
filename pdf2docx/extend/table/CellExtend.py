from pdf2docx.table.Cell import Cell


class CellExtend:
    def __init__(self, cell: Cell, row_index, col_index):
        self._cell = cell
        self.row_index = row_index
        self.col_index = col_index

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