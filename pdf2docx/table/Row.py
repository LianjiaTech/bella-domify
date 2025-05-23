# -*- coding: utf-8 -*-

'''Row in a table.
'''

from .Cells import Cells
from ..common.Element import Element


class Row(Element):
    '''Row in a table.'''
    def __init__(self, raw:dict=None):
        if raw is None: raw = {}
        super().__init__(raw)

        # logical row height
        self.height = raw.get('height', 0.0)

        # cells in row
        self._cells = Cells(parent=self).restore(raw.get('cells', []))


    def __getitem__(self, idx):
        try:
            cell = self._cells[idx]
        except IndexError:
            msg = f'Cell index {idx} out of range'
            raise IndexError(msg)
        else:
            return cell

    def __iter__(self):
        return (cell for cell in self._cells)

    def __len__(self):
        return len(self._cells)


    def append(self, cell):
        '''Append cell to row and update bbox accordingly.'''
        self._cells.append(cell)


    def store(self):
        res = super().store()
        res.update({
            'height': self.height,
            'cells': self._cells.store()
        })

        return res