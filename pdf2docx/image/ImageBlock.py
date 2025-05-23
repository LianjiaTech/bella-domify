# -*- coding: utf-8 -*-

'''Definition of Image block objects. 

**The raw image block will be merged into TextBlock > Line > Span.**
'''

from .Image import Image
from .ImageSpan import ImageSpan
from ..common.Block import Block
from ..text.Line import Line
from ..text.TextBlock import TextBlock


class ImageBlock(Image, Block):
    '''Image block.'''
    def __init__(self, raw:dict=None):
        super().__init__(raw)

        # inline image type by default
        self.set_inline_image_block()


    def to_text_block(self):
        """Convert image block to a span under text block.

        Returns:
            TextBlock: New TextBlock instance containing this image.
        """
        # image span
        span = ImageSpan().from_image(self)

        # add span to line
        image_line = Line()
        image_line.add(span)
        
        # insert line to block
        block = TextBlock()        
        block.add(image_line)

        # NOTE: it's an image block even though in TextBlock type
        block.set_inline_image_block() 

        return block
 

    def store(self):
        '''Store ImageBlock instance in raw dict.'''
        res = Block.store(self)
        res.update(
            Image.store(self)
        )
        return res

    
    def plot(self, page):
        '''Plot image bbox with diagonal lines (for debug purpose).
        
        Args: 
            page (fitz.Page): pdf page to plot.
        '''
        super().plot(page, color=(1,0,0))

    def extend_plot(self, page):
        self.plot(page)