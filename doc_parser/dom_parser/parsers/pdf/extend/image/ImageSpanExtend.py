import re

from doc_parser.dom_parser.parsers.pdf.extend.common.RelationConstruct import RelationElement
from doc_parser.dom_parser.parsers.pdf.image.ImageSpan import ImageSpan


def search_caption(block):
    '''Check if block is table caption.'''
    pattern = r'^\s*(图|Figure|figure|Fig|fig)\s*[0-9|-]+'
    if block and (match := re.match(pattern, block.block.text)):
        block.is_figure_name = 1
        return match[0]
    return None


class ImageSpanExtend(RelationElement):
    def __init__(self, image_span: ImageSpan):
        self.image_span = image_span
        self.caption_block  = None
        self.image_caption: str = None
        self.refed_blocks = []


    def relation_construct(self, cur_page, pages ):
        self.caption_block, self.image_caption = self.search_image_caption(cur_page)
        self.refed_blocks = self.search_image_reference(pages)

    def search_image_caption(self, cur_page ):
        '''Get image caption.'''
        blocks = []
        image_block_index = None
        for section in cur_page.sections:
            for column in section:
                for block in column.blocks:
                    if block.block.is_text_block:
                        blocks.append(block)
                        for line in block.lines:
                            if self.image_span in line.line.image_spans:
                                image_block_index = len(blocks) - 1  # index of image span in blocks

        caption_block, image_caption = None, None
        # search 2 blocks before and after image block
        for i in range(1, 3):
            prev_block, next_block = None, None
            if image_block_index - i > 0:
                prev_block = blocks[image_block_index - i]
            if image_block_index + i < len(blocks):
                next_block = blocks[image_block_index + i]
            if not prev_block and not next_block:
                break
            if prev_block and search_caption(prev_block):
                caption_block = prev_block
                image_caption = search_caption(prev_block)
                break
            if next_block and search_caption(next_block):
                caption_block = next_block
                image_caption = search_caption(next_block)
                break
        return caption_block, image_caption

    def search_image_reference(self, pages):
        '''Search table reference in all pages.'''
        ref_blocks = []
        if not self.caption_block:
            return ref_blocks
        for page in pages:
            for section in page.sections:
                for column in section:
                    for block in column.blocks:
                        if block.is_text_block:
                            if self.image_caption in block.block.text and block != self.caption_block:
                                ref_blocks.append(block)
                                block.add_ref_image(self.image_span)
        return ref_blocks
