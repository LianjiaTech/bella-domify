from pdf2docx.image.ImageSpan import ImageSpan
from pdf2docx.page.Page import Page
from pdf2docx.page.Pages import Pages
from pdf2docx.text.TextBlock import TextBlock
import re


def search_caption(block: TextBlock):
    '''Check if block is table caption.'''
    """for figure caption, it should contains word like 图， Figure, Fig, 
    with zeor or more space and zero or more number"""
    pattern = r'(图|Figure|Fig)[\s]*[0-9]+'
    match = re.match(pattern, block.text)
    return match[0] if match else None


class ImageSpanExtend:
    def __init__(self, image_span: ImageSpan, page_of_image: Page, pages: Pages):
        self.image_span = image_span
        self.page_of_image = page_of_image  # image span is in which page
        self.all_pages = pages
        self.caption_block, self.image_caption = self.search_image_caption()
        self.ref_blocks = self.search_image_reference()

    def search_image_caption(self):
        '''Get image caption.'''
        blocks = []
        image_block_index = None
        for section in self.page_of_image.sections:
            for column in section:
                for block in column.blocks:
                    if block.is_text_block:
                        blocks.append(block)
                        for line in block.lines:
                            if self.image_span in line.image_spans:
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

    def search_image_reference(self):
        '''Search table reference in all pages.'''
        ref_blocks = []
        if not self.caption_block:
            return ref_blocks
        for page in self.all_pages:
            for section in page.sections:
                for column in section:
                    for block in column.blocks:
                        if block.is_text_block:
                            if self.image_caption in block.text and block != self.caption_block:
                                ref_blocks.append(block)
        return ref_blocks
