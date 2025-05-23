# -*- coding: utf-8 -*-

'''Section of Page.

In most cases, one section per page. But in case multi-columns page, sections are used 
to distinguish these different layouts.

.. note::
    Currently, support at most two columns.

::

    {
        'bbox': (x0,y0,x1,y1)
        'num_cols': 1,
        'space': 0,
        'columns': [{
            ... # column properties
        }, ...]
    }
'''

from .Column import Column
from ..common.Collection import BaseCollection


class Section(BaseCollection):
    
    def __init__(self, space:int=0, columns:list=None, parent=None):
        """Initialize Section instance.

        Args:
            space (int, optional): Space between adjacent columns. Defaults to 0.
            columns (list, optional): A list of Column instances. Defaults to None.
            parent (Sections, optional): Parent element. Defaults to None.
        """
        self.space = space
        self.before_space = 0.0
        super().__init__(columns, parent)
    

    @property
    def num_cols(self): return len(self)


    def store(self):
        '''Store parsed section layout in dict format.'''
        return {
            'bbox'   : tuple([x for x in self.bbox]),
            'num_cols'   : self.num_cols,
            'space'  : self.space,
            'before_space'  : self.before_space,
            'columns': super().store()
        }
    

    def restore(self, raw:dict):
        '''Restore section from source dict.'''
        # bbox is maintained automatically based on columns
        self.space = raw.get('space', 0)   # space between adjacent columns
        self.before_space = raw.get('before_space', 0)   # space between adjacent columns

        # get each column
        for raw_col in raw.get('columns', []):
            column = Column().restore(raw_col)
            self.append(column)

        return self


    def parse(self, **settings):
        '''Parse section layout.'''
        for column in self:
            column.parse(**settings)
        return self