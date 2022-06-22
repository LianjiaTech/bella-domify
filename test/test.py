# -*- coding: utf-8 -*-

'''
To test the pdf conversion and converting quality, the idea is to convert generated docx to pdf,
then check the image similarity between source pdf page and converted pdf page. Considering the 
converting quality from docx to pdf, a Windows-based command line tool `OfficeToPDF` is used, in
addition, an installation of Microsoft Word is required.

To leverage the benefit of Github Action, the testing process is divided into three parts:
  1. Convert sample pdf to docx with `pdf2docx`.
  2. Convert generated docx to pdf for comparing. 
  3. Convert page to image and compare similarity with `python-opencv`.

Test scripts on Part One and Three are applied with two test class respectively in this module,
so they could be run seperately with pytest command, e.g.

- pytest -vs --no-header test.py::TestConversion for Part One
- pytest -vs --no-header test.py::TestQuality for Part Three

Links on MS Word to PDF conversion:
  - https://github.com/cognidox/OfficeToPDF/releases
  - https://github.com/AndyCyberSec/pylovepdf
  - https://www.e-iceblue.com/Tutorials/Java/Spire.Doc-for-Java/Program-Guide/Conversion/Convert-Word-to-PDF-in-Java.html
'''

import os
from pdf2docx import Converter, parse
from pdf2docx.text.TextSpan import TextSpan


script_path = os.path.abspath(__file__) # current script path

class Utility:
    '''utilities related directly to the test case'''

    @property
    def test_dir(self): return os.path.dirname(script_path)

    @property
    def layout_dir(self): return os.path.join(self.test_dir, 'layouts')

    @property
    def sample_dir(self): return os.path.join(self.test_dir, 'samples')

    @property
    def output_dir(self): return os.path.join(self.test_dir, 'outputs')

    def init_test(self, filename):
        ''' Initialize parsed layout and benchmark layout.'''
        # parsed layout: first page only
        pdf_file = os.path.join(self.sample_dir, f'{filename}.pdf')
        docx_file = os.path.join(self.output_dir, f'{filename}.docx')
        cv = Converter(pdf_file)        
        cv.convert(docx_file, pages=[0])
        self.test = cv[0].sections
        cv.close()

        # restore sample layout
        cv = Converter(pdf_file)
        layout_file = os.path.join(self.layout_dir, f'{filename}.json')
        cv.deserialize(layout_file)
        self.sample = cv[0].sections

        return self


    def verify_layout(self, threshold=0.95):
        ''' Check layout between benchmark and parsed one.'''
        # count of sections
        m, n = len(self.sample), len(self.test)
        assert m==n, f"\nThe count of parsed sections '{n}' is inconsistent with sample '{m}'"

        for s_section, t_section in zip(self.sample, self.test):
            # count of columns
            m, n = len(s_section), len(t_section)
            assert m==n, f"\nThe count of parsed columns '{n}' is inconsistent with sample '{m}'"

            for s_col, t_col in zip(s_section, t_section):
                Utility._verify_layout(s_col.blocks, t_col.blocks, threshold)
    

    @staticmethod
    def _verify_layout(sample_blocks, test_blocks, threshold):
        ''' Check layout between benchmark and parsed one.'''
        sample_text_image_blocks = sample_blocks.text_blocks
        test_text_image_blocks = test_blocks.text_blocks
        
        # text blocks
        f = lambda block: block.is_text_block
        sample_text_blocks = list(filter(f, sample_text_image_blocks))
        test_text_blocks   = list(filter(f, test_text_image_blocks))
        Utility._check_text_layout(sample_text_blocks, test_text_blocks, threshold)

        # inline images
        sample_inline_images = sample_blocks.inline_image_blocks
        test_inline_images = test_blocks.inline_image_blocks
        Utility._check_inline_image_layout(sample_inline_images, test_inline_images, threshold)

        # floating images
        f = lambda block: block.is_float_image_block
        sample_float_images = list(filter(f, sample_text_image_blocks))
        test_float_images = list(filter(f, test_text_image_blocks))
        Utility._check_float_image_layout(sample_float_images, test_float_images, threshold)        

        # table blocks
        sample_tables = sample_blocks.table_blocks
        test_tables = test_blocks.table_blocks        
        Utility._check_table_layout(sample_tables, test_tables, threshold)


    def _check_table_layout(self, threshold):
        '''Check table layout.
             - table contents are covered by text layout checking
             - check table structure
        '''
        sample_tables = self.sample.blocks.table_blocks
        test_tables = self.test.blocks.table_blocks

        # count of tables
        m, n = len(sample_tables), len(test_tables)
        assert m==n, f"\nThe count of parsed tables '{n}' is inconsistent with sample '{m}'"

        # check structures table by table
        for sample_table, test_table in zip(sample_tables, test_tables):
            for sample_row, test_row in zip(sample_table, test_table):
                for sample_cell, test_cell in zip(sample_row, test_row):
                    if not sample_cell: continue
                    matched, msg = test_cell.compare(sample_cell, threshold)
                    assert matched, f'\n{msg}'


    def _check_inline_image_layout(self, threshold):
        '''Check image layout: bbox and vertical spacing.'''
        sample_image_spans = self.sample.blocks.image_spans(level=1)
        test_image_spans = self.test.blocks.image_spans(level=1)

        # count of images
        m, n = len(sample_image_spans), len(test_image_spans)
        assert m==n, f"\nThe count of image blocks {n} is inconsistent with sample {m}"

        # check each image
        for sample, test in zip(sample_image_spans, test_image_spans):
            matched, msg = test.compare(sample, threshold)
            assert matched, f'\n{msg}'
    

    def _check_float_image_layout(self, threshold):
        '''Check image layout: bbox and vertical spacing.'''
        sample_float_images = self.sample.blocks.floating_image_blocks
        test_float_images = self.test.blocks.floating_image_blocks

        # count of images
        m, n = len(sample_float_images), len(test_float_images)
        assert m==n, f"\nThe count of image blocks {n} is inconsistent with sample {m}"

        # check each image
        for sample, test in zip(sample_float_images, test_float_images):
            matched, msg = test.compare(sample, threshold)
            assert matched, f'\n{msg}'


    def _check_text_layout(self, threshold):
        ''' Compare text layout and format. 
             - text layout is determined by vertical spacing
             - text format is defined in style attribute of TextSpan
        '''
        sample_text_blocks = self.sample.blocks.text_blocks(level=1)
        test_text_blocks = self.test.blocks.text_blocks(level=1)

        # count of blocks
        m, n = len(sample_text_blocks), len(test_text_blocks)
        assert m==n, f"\nThe count of text blocks {n} is inconsistent with sample {m}"
        
        # check layout of each block
        for sample, test in zip(sample_text_blocks, test_text_blocks):

            # text bbox and vertical spacing
            matched, msg = test.compare(sample, threshold)
            assert matched, f'\n{msg}'

            # text style
            for sample_line, test_line in zip(sample.lines, test.lines):
                for sample_span, test_span in zip(sample_line.spans, test_line.spans):
                    if not isinstance(sample_span, TextSpan): continue
                    
                    # text
                    a, b = sample_span.text, test_span.text
                    assert a==b, f"\nApplied text '{b}' is inconsistent with sample '{a}'"

                    # style
                    m, n = len(sample_span.style), len(test_span.style)
                    assert m==n, f"\nThe count of applied text style {n} is inconsistent with sample {m}"

                    sample_span.style.sort(key=lambda item: item['type'])
                    test_span.style.sort(key=lambda item: item['type'])
                    for sample_dict, test_dict in zip(sample_span.style, test_span.style):
                        a, b = sample_dict['type'], test_dict['type']
                        assert a==b, f"\nApplied text style '{b}' is inconsistent with sample '{a}'"


class Test_Main(Utility):
    '''Main text class.'''

    def setup(self):
        # create output path if not exist
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

    def test_blank_file(self):
        '''sample file without any texts or images.'''
        self.init_test('demo-blank').verify_layout(threshold=0.95)

    def test_text_format(self):
        '''sample file focusing on text format, e.g. highlight, underline, strike-through.'''
        self.init_test('demo-text').verify_layout(threshold=0.95)

    def test_text_alignment(self):
        '''test text alignment.'''
        self.convert('demo-text-alignment')    
    
    def test_unnamed_fonts(self):
        '''test unnamed fonts which destroys span bbox, and accordingly line/block layout.'''
        self.convert('demo-text-unnamed-fonts')

    def test_text_scaling(self):
        '''test font size. In this case, the font size is set precisely with character scaling.'''
        self.convert('demo-text-scaling')
    
    def test_text_hidden(self):
        '''test hidden text, which is ignore by default.'''
        self.convert('demo-text-hidden')

    # ------------------------------------------
    # image styles
    # ------------------------------------------
    def test_image(self):
        '''sample file focusing on inline-image.'''
        self.init_test('demo-image').verify_layout(threshold=0.95)

    def test_vector_graphic(self):
        '''sample file focusing on vector graphic.'''
        self.init_test('demo-image-vector-graphic').verify_layout(threshold=0.95)

    def test_image_cmyk(self):
        '''sample file focusing on image in CMYK color-space.'''
        self.init_test('demo-image-cmyk').verify_layout(threshold=0.95)

    def test_image_transparent(self):
        '''test transparent images.'''
        self.convert('demo-image-transparent')
    
    def test_image_rotation(self):
        '''test rotating image due to pdf page rotation.'''
        self.convert('demo-image-rotation')

    def test_image_overlap(self):
        '''test images with both intersection and page rotation.'''
        self.convert('demo-image-overlap')


    def test_table_bottom(self):
        '''sample file focusing on page break due to table at the end of page.'''
        self.init_test('demo-table-bottom').verify_layout(threshold=0.95)

    def test_table_format(self):
        '''sample file focusing on table format, e.g. 
            - border and shading style
            - vertical cell
            - merged cell
            - text format in cell
        '''
        self.init_test('demo-table').verify_layout(threshold=0.95)

    def test_stream_table(self):
        '''sample file focusing on stream structure and shading.'''
        self.init_test('demo-table-stream').verify_layout(threshold=0.95)

    def test_table_shading(self):
        '''sample file focusing on simulating shape with shading cell.'''
        self.init_test('demo-table-shading').verify_layout(threshold=0.95)
    
    def test_table_shading_highlight(self):
        '''test distinguishing table shading and highlight.'''
        self.init_test('demo-table-shading-highlight').verify_layout(threshold=0.95)

    def test_lattice_table(self):
        '''sample file focusing on lattice table with very close text underlines to table borders.'''
        self.init_test('demo-table-close-underline').verify_layout(threshold=0.95)

    def test_table_border_style(self):
        '''sample file focusing on border style, e.g. width, color.'''
        self.init_test('demo-table-border-style').verify_layout(threshold=0.95)

    def test_table_align_borders(self):
        '''sample file focusing on aligning stream table borders to simplify table structure.'''
        self.init_test('demo-table-align-borders').verify_layout(threshold=0.95)

    def test_nested_table(self):
        '''sample file focusing on nested tables.'''
        self.init_test('demo-table-nested').verify_layout(threshold=0.95)

    def test_text_scaling(self):
        '''sample file focusing on font size.
            In this case, the font size is set precisely with character scaling.
        '''
        self.init_test('demo-text-scaling').verify_layout(threshold=0.95)

    def test_path_transformation(self):
        '''test path transformation. In this case, the (0,0) origin is out of the page.'''
        self.init_test('demo-path-transformation').verify_layout(threshold=0.95)


    # ------------------------------------------
    # table contents
    # ------------------------------------------
    def test_extracting_table(self):
        '''test extracting contents from table.'''
        filename = 'demo-table'
        pdf_file = os.path.join(self.sample_dir, f'{filename}.pdf')
        tables = Converter(pdf_file).extract_tables(end=1)
        print(tables)

        # compare the last table
        sample = [
            ['Input', None, None, None, None, None],
            ['Description A', 'mm', '30.34', '35.30', '19.30', '80.21'],
            ['Description B', '1.00', '5.95', '6.16', '16.48', '48.81'],
            ['Description C', '1.00', '0.98', '0.94', '1.03', '0.32'],
            ['Description D', 'kg', '0.84', '0.53', '0.52', '0.33'],
            ['Description E', '1.00', '0.15', None, None, None],
            ['Description F', '1.00', '0.86', '0.37', '0.78', '0.01']
        ]
        assert tables[-1]==sample

    
    # ------------------------------------------
    # command line arguments
    # ------------------------------------------
    def test_multi_pages(self):
        '''test converting pdf with multi-pages.'''
        filename = 'demo'
        pdf_file = os.path.join(self.sample_dir, f'{filename}.pdf')
        docx_file = os.path.join(self.output_dir, f'{filename}.docx')    
        parse(pdf_file, docx_file, start=1, end=5)

        # check file        
        assert os.path.isfile(docx_file)
    


class TestQuality:
    '''Check the quality of converted docx. 
    Note the docx files must be converted to PDF files in advance.
    '''

    INDEX_MAP = {
        'demo-blank.pdf': 1.0,
        'demo-image-cmyk.pdf': 0.90,
        'demo-image-transparent.pdf': 0.90,
        'demo-image-vector-graphic.pdf': 0.90,
        'demo-image.pdf': 0.90,
        'demo-image-rotation.pdf': 0.90,
        'demo-image-overlap.pdf': 0.90,
        'demo-path-transformation.pdf': 0.90,
        'demo-section-spacing.pdf': 0.90,
        'demo-section.pdf': 0.70,
        'demo-table-align-borders.pdf': 0.49,
        'demo-table-border-style.pdf': 0.90,
        'demo-table-bottom.pdf': 0.90,
        'demo-table-close-underline.pdf': 0.59,
        'demo-table-lattice-one-cell.pdf': 0.79,
        'demo-table-lattice.pdf': 0.75,
        'demo-table-nested.pdf': 0.84,
        'demo-table-shading-highlight.pdf': 0.60,
        'demo-table-shading.pdf': 0.80,
        'demo-table-stream.pdf': 0.55,
        'demo-table.pdf': 0.90,
        'demo-text-alignment.pdf': 0.90,
        'demo-text-scaling.pdf': 0.80,
        'demo-text-unnamed-fonts.pdf': 0.80,
        'demo-text-hidden.pdf': 0.90,
        'demo-text.pdf': 0.80
    }

    def setup(self):
        '''create output path if not exist.'''
        if not os.path.exists(output_path): os.mkdir(output_path)


    def test_quality(self):
        '''Convert page to image and compare similarity.'''
        for filename in os.listdir(output_path):
            if not filename.endswith('pdf'): continue

            source_pdf_file = os.path.join(sample_path, filename)
            target_pdf_file = os.path.join(output_path, filename)

            # open pdf    
            source_pdf = fitz.open(source_pdf_file)
            target_pdf = fitz.open(target_pdf_file)

            # compare page count
            if len(source_pdf)>1: continue # one page sample only
            assert len(target_pdf)==1, f"\nThe page count of {filename} is incorrect."

            # compare the first page
            sidx = get_page_similarity(target_pdf[0], source_pdf[0])
            threshold = TestQuality.INDEX_MAP.get(filename, 0.80)
            print(f'Checking {filename}: {sidx} v.s. {threshold}')
            assert sidx>=threshold, 'Significant difference might exist since similarity index is lower than threshold.'
