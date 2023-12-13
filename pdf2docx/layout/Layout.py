# -*- coding: utf-8 -*-

'''Document layout depends on Blocks and Shapes.

**Layout** here refers to the content and position of text, image and table. The target is to convert
source blocks and shapes to a *flow layout* that can be re-created as docx elements like paragraph and
table. In addition to ``Section`` and ``Column``, ``TableBlock`` is used to maintain the page layout . 
So, detecting and parsing table block is the principle steps.

The prerequisite work is done before this step:

1. Clean up source blocks and shapes in Page level, e.g. convert source blocks to ``Line`` level,
   because the block structure determined by ``PyMuPDF`` might be not reasonable.
#. Parse structure in document level, e.g. page header/footer.
#. Parse Section and Column layout in Page level. 

The page layout parsing idea:

1. Parse table layout in Column level.
    (a) Detect explicit tables first based on shapes. 
    (#) Then, detect stream tables based on original text blocks and parsed explicit tables.
    (#) Move table contained blocks (lines or explicit table) to associated cell-layout.
#. Parse paragraph in Column level.
    (a) Detect text blocks by combining related lines.
    (#) Parse paragraph style, e.g. text format, alignment
#. Calculate vertical spacing based on parsed tables and paragraphs.
#. Repeat above steps for cell-layout in parsed table level.
'''

from ..text.Line import Line
from ..common import constants
from ..shape.Shapes import Shapes


class Layout:
    '''Blocks and shapes structure and formats.'''

    def __init__(self, blocks=None, shapes=None):
        ''' Initialize layout.

        Args:
            blocks (Blocks): Blocks representing text/table contents.
            shapes (Shapes): Shapes representing table border, shading and text style like underline, highlight.
            parent (Page, Column, Cell): The object that this layout belonging to.
        '''
        from .Blocks import Blocks # avoid import conflicts
        from ..table.TablesConstructor import TablesConstructor

        self.blocks = Blocks(instances=blocks, parent=self)
        self.shapes = Shapes(instances=shapes, parent=self)        
        self._table_parser = TablesConstructor(parent=self) # table parser


    def working_bbox(self, *args, **kwargs):
        '''Working bbox of current Layout.'''
        raise NotImplementedError


    def contains(self, *args, **kwargs):
        '''Whether given element is contained in this layout.'''
        raise NotImplementedError


    def store(self):
        '''Store parsed layout in dict format.'''
        return {
            'blocks': self.blocks.store(),
            'shapes': self.shapes.store()
        }


    def restore(self, data:dict):
        '''Restore Layout from parsed results.'''
        if data.get('blocks'):
            self._assign_pseudo_bold(data)
        self.blocks.restore(data.get('blocks', []))

        self.shapes.restore(data.get('shapes', []))
        return self

    def _assign_pseudo_bold(self, data:dict):
        # 将从text_trace中获取到的底层伪粗体信息，附加到span上
        spans = []
        for block in data.get('blocks'):
            if 'lines' not in block: continue
            for line in block['lines']:
                if 'spans' not in line: continue
                spans.extend(line['spans'])
        spans = [(span, ''.join([char['c'] for char in span['chars']])) for span in spans]
        pseudo_bold = data.get('pseudo_bold')
        spans_index, pseudo_bold_index = 0, 0 # spans和pseudo_bold的搜索索引
        while True:
            if spans_index >= len(spans): break
            if pseudo_bold_index >= len(pseudo_bold): break
            span_text = spans[spans_index][1]
            pseudo_bold_span_text = ''
            span_font_pseubo_bold = False
            while pseudo_bold_index < len(pseudo_bold):
                pseudo_bold_span_text += pseudo_bold[pseudo_bold_index].chars
                # 如果span_text以pseudo_bold_span_text开头，或者span_text包含pseudo_bold_span_text，且伪粗体标记与上一个伪粗体标记相同
                # 则pseudo_bold_index对应的span属于spans_index对应的span
                if span_text.startswith(pseudo_bold_span_text) or (
                        pseudo_bold[pseudo_bold_index].chars in span_text and
                        span_font_pseubo_bold == pseudo_bold[pseudo_bold_index].pseudo_bold
                ):
                    span_font_pseubo_bold = pseudo_bold[pseudo_bold_index].pseudo_bold
                    pseudo_bold_index += 1
                else:
                    break
            # 添加伪粗体标记
            spans[spans_index][0]['pseudo_bold'] = span_font_pseubo_bold
            spans_index += 1

    def assign_blocks(self, blocks:list):
        '''Add blocks (line or table block) to this layout. 
        
        Args:
            blocks (list): a list of text line or table block to add.
        
        .. note::
            If a text line is partly contained, it must deep into span -> char.
        '''
        for block in blocks: self._assign_block(block)


    def assign_shapes(self, shapes:list):
        '''Add shapes to this cell. 
        
        Args:
            shapes (list): a list of Shape instance to add.
        '''
        # add shape if contained in cell
        for shape in shapes:
            if self.working_bbox.intersects(shape.bbox): self.shapes.append(shape)


    def parse(self, **settings):
        '''Parse layout.

        Args:
            settings (dict): Layout parsing parameters.
        '''
        if not self.blocks: return

        # parse tables
        self._parse_table(**settings)

        # parse paragraphs
        self._parse_paragraph(**settings)

        # parse sub-layout, i.e. cell layouts under table block
        for block in filter(lambda e: e.is_table_block, self.blocks):
            block.parse(**settings)


    def _assign_block(self, block):
        '''Add block (line or table block) to this layout.'''
        # add block directly if fully contained in cell
        if self.contains(block, threshold=constants.FACTOR_MAJOR):
            self.blocks.append(block)
        
        # deep into line span if any intersection
        elif self.bbox & block.bbox and isinstance(block, Line):
            self.blocks.append(block.intersects(self.bbox))


    def _parse_table(self, **settings):
        '''Parse table layout: 
        
        * detect explicit tables first based on shapes, 
        * then stream tables based on original text blocks and parsed explicit tables;
        * move table contained blocks (text block or explicit table) to associated cell layout.
        '''        
        # parse table structure/format recognized from explicit shapes
        if settings['parse_lattice_table']:
            self._table_parser.lattice_tables(
                settings['connected_border_tolerance'],
                settings['min_border_clearance'],
                settings['max_border_width'])
        
        # parse table structure based on implicit layout of text blocks
        if settings['parse_stream_table']:
            self._table_parser.stream_tables(
                settings['min_border_clearance'],
                settings['max_border_width'],
                settings['line_separate_threshold'])
    

    def _parse_paragraph(self, **settings):
        '''Create text block based on lines, and parse text format, e.g. text highlight, 
        paragraph indentation '''
        # group lines to text block
        self.blocks.parse_block(
            settings['max_line_spacing_ratio'],
            settings['line_break_free_space_ratio'],
            settings['new_paragraph_free_space_ratio'])

        # parse text format, e.g. highlight, underline
        self.blocks.parse_text_format(
            self.shapes.text_style_shapes,
            settings['delete_end_line_hyphen'])
        
        # paragraph / line spacing
        self.blocks.parse_spacing(
            settings['line_separate_threshold'],
            settings['line_break_width_ratio'],
            settings['line_break_free_space_ratio'],
            settings['lines_left_aligned_threshold'],
            settings['lines_right_aligned_threshold'],
            settings['lines_center_aligned_threshold'])