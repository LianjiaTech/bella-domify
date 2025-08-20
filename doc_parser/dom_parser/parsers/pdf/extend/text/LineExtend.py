from doc_parser.dom_parser.parsers.pdf.common.Element import Element
from doc_parser.dom_parser.parsers.pdf.extend.common.RelationConstruct import RelationElement
from doc_parser.dom_parser.parsers.pdf.extend.image.ImageSpanExtend import ImageSpanExtend
from doc_parser.dom_parser.parsers.pdf.image.ImageSpan import ImageSpan
from doc_parser.dom_parser.parsers.pdf.page import Page
from doc_parser.dom_parser.parsers.pdf.page.Pages import Pages
from doc_parser.dom_parser.parsers.pdf.text.Line import Line
from doc_parser.dom_parser.parsers.pdf.text.TextSpan import TextSpan


class LineExtend(Element, RelationElement):
    def __init__(self, line: Line):
        raw = {'bbox': (line.bbox.x0, line.bbox.y0, line.bbox.x1, line.bbox.y1)}
        super().__init__(raw=raw, parent=line._parent)
        self.line = line
        self.spans = []
        for span in self.line.spans:
            if isinstance(span, TextSpan):
                self.spans.append(span)
            elif isinstance(span, ImageSpan):
                self.spans.append(ImageSpanExtend(span))

    def relation_construct(self, cur_page: Page, pages: Pages):
        for span in self.spans:
            if isinstance(span, ImageSpanExtend):
                span.relation_construct(cur_page, pages)

    @property
    def image_spans(self):
        return [span for span in self.spans if isinstance(span, ImageSpanExtend)]

    @property
    def text(self) -> str:
        return self.line.text

    @property
    def raw_text(self) -> str:
        return self.line.raw_text
    
    @property
    def is_catalog(self):
        return self.line.is_catalog
