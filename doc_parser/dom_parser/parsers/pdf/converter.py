# -*- coding: utf-8 -*-
import fitz

from doc_parser.context import logger_context
from doc_parser.dom_parser.domtree.domtree import DomTreeModel
from doc_parser.dom_parser.parsers.base import BaseConverter
from doc_parser.dom_parser.parsers.pdf.config import DEFAULT_SETTINGS
from doc_parser.dom_parser.parsers.pdf.domtree_parser import PDFDomTreeParser
from doc_parser.dom_parser.parsers.pdf.extend.page.PagesExtend import PagesExtend
from doc_parser.dom_parser.parsers.pdf.page.Page import Page
from doc_parser.dom_parser.parsers.pdf.page.Pages import Pages

# check PyMuPDF>=1.19.x
if list(map(int, fitz.VersionBind.split("."))) < [1, 19, 0]:
    raise SystemExit("PyMuPDF>=1.19.0 is required for dom_parser.")

logger = logger_context.get_logger()


class PDFConverter(BaseConverter):
    '''The ``PDF`` to ``docx`` converter.
    
    * Read PDF file with ``PyMuPDF`` to get raw layout data page by page, including text,
      image, drawing and its properties, e.g. boundary box, font, size, image width, height.
    * Analyze layout in document level, e.g. page header, footer and margin.
    * Parse page layout to docx structure, e.g. paragraph and its properties like indentation, 
      spacing, text alignment; table and its properties like border, shading, merging. 
    * Finally, generate docx with ``python-docx``.
    '''

    def __init__(
            self, pdf_file: str = None, password: str = None, stream: bytes = None
    ):
        '''Initialize fitz object with given pdf file path.

        Args:
            pdf_file (str): pdf file path.
            stream   (bytes): pdf file in memory.
            password (str): Password for encrypted pdf. Default to None if not encrypted.
        '''
        # fitz object
        self.filename_pdf = pdf_file
        self.password = str(password or "")

        if not pdf_file and not stream:
            raise ValueError("Either pdf_file or stream must be given.")

        if stream:
            self._fitz_doc = fitz.Document(stream=stream)

        else:
            self._fitz_doc = fitz.Document(pdf_file)

        # initialize empty pages container
        self._pages = Pages()

    @property
    def fitz_doc(self):
        return self._fitz_doc

    @property
    def pages(self):
        return self._pages

    @property
    def pages_extend(self):
        return self._pages_extend

    def close(self):
        self._fitz_doc.close()

    @property
    def default_settings(self):
        '''Default parsing parameters.'''
        return DEFAULT_SETTINGS

    # -----------------------------------------------------------------------
    # Parsing process: load -> analyze document -> parse pages -> make docx
    # -----------------------------------------------------------------------

    def parse(self, start: int = 0, end: int = None, pages: list = None, **kwargs):
        '''Parse pages in three steps:
        * open PDF file with ``PyMuPDF``
        * analyze whole document, e.g. page section, header/footer and margin
        * parse specified pages, e.g. paragraph, image and table

        Args:
            start (int, optional): First page to process. Defaults to 0, the first page.
            end (int, optional): Last page to process. Defaults to None, the last page.
            pages (list, optional): Range of page indexes to parse. Defaults to None.
            kwargs (dict, optional): Configuration parameters.


        parse_document
        包含 list的识别

        parse_pages
        递归解析：包含line的合并和拆分


        '''
        self.load_pages(start, end, pages, **kwargs) \
            .parse_document(**kwargs) \
            .parse_pages(**kwargs) \
            .relation_construct(**kwargs)


        return self

    def load_pages(self, start: int = 0, end: int = None, pages: list = None, **kwargs):
        '''Step 1 of converting process: open PDF file with ``PyMuPDF``, 
        especially for password encrypted file.
        
        Args:
            start (int, optional): First page to process. Defaults to 0, the first page.
            end (int, optional): Last page to process. Defaults to None, the last page.
            pages (list, optional): Range of page indexes to parse. Defaults to None.
        '''
        logger.info(self._color_output('[1/4] Opening document...'))

        # encrypted pdf ?
        if self._fitz_doc.needs_pass:
            if not self.password:
                raise ConversionException(f'Require password for {self.filename_pdf}.')

            elif not self._fitz_doc.authenticate(self.password):
                raise ConversionException('Incorrect password.')

        # initialize empty pages
        num = len(self._fitz_doc)
        self._pages.reset([Page(id=i, skip_parsing=True) for i in range(num)])

        # set pages to parse
        page_indexes = self._page_indexes(start, end, pages, num)
        for i in page_indexes:
            self._pages[i].skip_parsing = False
        if kwargs['remove_watermark']:
            for page in self.fitz_doc.pages():
                self.remove_watermark(page)
        return self

    def parse_document(self, **kwargs):
        '''Step 2 of converting process: analyze whole document, e.g. page section,
        header/footer and margin.'''
        logger.info(self._color_output('[2/4] Analyzing document...'))

        self._pages.parse(self.fitz_doc, **kwargs)

        return self

    def parse_pages(self, **kwargs):
        '''Step 3 of converting process: parse pages, e.g. paragraph, image and table.'''
        logger.info(self._color_output('[3/4] Parsing pages...'))

        pages = [page for page in self._pages if not page.skip_parsing]
        num_pages = len(pages)
        for i, page in enumerate(pages, start=1):
            pid = page.id + 1
            logger.info('(%d/%d) Page %d', i, num_pages, pid)
            try:
                page.parse(**kwargs)
            except Exception as e:
                if not kwargs['debug'] and kwargs['ignore_page_error']:
                    logger.error('Ignore page %d due to parsing page error: %s', pid, e)
                else:
                    raise ConversionException(f'Error when parsing page {pid}: {e}')

        return self

    def relation_construct(self, **kwargs):
        logger.info(self._color_output('[4/4] Build elements relations...'))
        # 页面扩展对象
        self._pages_extend = PagesExtend(self._pages)
        self.pages_extend.relation_construct()
        return self


    # -----------------------------------------------------------------------
    # high level methods, e.g. convert, extract table
    # -----------------------------------------------------------------------

    def dom_tree_parse(self, start: int = 0, end: int = None, pages: list = None, **kwargs):
        '''
        解析pdf文件，构建文档对象模型（DOM）树
        '''
        # 首先 解析页面
        settings = self.default_settings
        settings.update(kwargs)
        self.parse(start, end, pages, **settings)

        debug_file = fitz.Document(self.filename_pdf) if settings['debug'] else None
        # 筛选出最合适最合适的dom_tree
        dom_tree_parser = PDFDomTreeParser(self.pages_extend, debug_file, self._fitz_doc)
        dom_tree = dom_tree_parser.parse(**settings)  # 开始解析
        if settings['debug'] and debug_file:
            debug_file.save(kwargs['debug_file_name'])
        return dom_tree

    def extract_tables(self, start: int = 0, end: int = None, pages: list = None,
                       extract_table_with_cell_pos=False, **kwargs):
        '''Extract table contents from specified PDF pages.

        Args:
            start (int, optional): First page to process. Defaults to 0, the first page.
            end (int, optional): Last page to process. Defaults to None, the last page.
            pages (list, optional): Range of page indexes. Defaults to None.
            kwargs (dict, optional): Configuration parameters. Defaults to None.
        
        Returns:
            list: A list of parsed table content.
        '''
        # parsing pages first
        settings = self.default_settings
        settings.update(kwargs)
        settings['extract_table_with_cell_pos'] = extract_table_with_cell_pos
        self.parse(start, end, pages, **settings)

        # get parsed tables
        tables = []
        for page in self._pages:
            if page.finalized: tables.extend(page.extract_tables(**settings))

        if settings['debug']:
            logger.info('Extracted tables: %s', tables)
            self.plot(**settings)

        return tables

    def remove_watermark(self, page):
        """ see https://github.com/pymupdf/PyMuPDF/discussions/1855 """
        # 移除水印
        page.clean_contents()
        xref = page.get_contents()[0]  # get xref of resulting /Contents object
        cont = bytearray(page.read_contents())  # read the contents source as a (modifyable) bytearray
        if cont.find(b"/Subtype/Watermark") > 0:  # this will confirm a marked-content watermark is present
            print("marked-content watermark present")
        else:
            return  # no watermark found
        while True:
            i1 = cont.find(b"/Artifact")  # start of definition
            if i1 < 0: break  # none more left: done
            i2 = cont.find(b"EMC", i1)  # end of definition
            cont[i1 - 2: i2 + 3] = b""  # remove the full definition source "q ... EMC"
        page.parent.update_stream(xref, cont)  # replace the original source

    def plot(self, **kwargs):
        debug_file = fitz.Document(self.filename_pdf)
        for page, debug_page in zip(self.pages, debug_file.pages()):
            if page.skip_parsing:
                continue
            page.sections.extend_plot(debug_page)
        debug_file.save(kwargs['debug_file_name'])

    @staticmethod
    def _page_indexes(start, end, pages, pdf_len):
        '''Parsing arguments.'''
        if pages:
            indexes = [int(x) for x in pages]
        else:
            end = end or pdf_len
            s = slice(int(start), int(end))
            indexes = range(pdf_len)[s]

        return indexes

    @staticmethod
    def _color_output(msg):
        return f'\033[1;36m{msg}\033[0m'


class ConversionException(Exception):
    pass


class MakedocxException(ConversionException):
    pass
