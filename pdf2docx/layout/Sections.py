# -*- coding: utf-8 -*-

'''Collection of :py:class:`~pdf2docx.layout.Section` instances.
'''

from .Section import Section
from ..common.Collection import BaseCollection


class Sections(BaseCollection):

    def restore(self, raws:list):
        """Restore sections from source dicts."""
        self.reset()
        for raw in raws:
            section = Section().restore(raw)
            self.append(section)
        return self

    def parse(self, **settings):
        '''Parse layout under section level.'''
        for section in self:
            section.parse(**settings)
        return self

    def plot(self, page):
        '''Plot all section blocks for debug purpose.'''
        for section in self:
            for column in section:
                column.plot(page, stroke=(1,1,0), width=1.5) # column bbox
                column.blocks.plot(page) # blocks

    def extend_plot(self, page):
        '''Plot all section blocks for debug purpose.'''
        for section in self:
            for column in section:
                try:
                    column.blocks.extend_plot(page)
                except AttributeError as e:
                    print(e)