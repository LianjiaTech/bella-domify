from pdf2docx.common.Element import Element
from pdf2docx.extend.common.RelationConstruct import RelationElement
from pdf2docx.extend.image.ImageSpanExtend import ImageSpanExtend
from pdf2docx.image.ImageSpan import ImageSpan
from pdf2docx.page import Page
from pdf2docx.page.Pages import Pages
from pdf2docx.text.Line import Line
from pdf2docx.text.TextSpan import TextSpan


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
