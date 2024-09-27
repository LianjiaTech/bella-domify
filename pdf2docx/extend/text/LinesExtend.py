from __future__ import annotations
from pdf2docx.common.Collection import ElementCollection
from pdf2docx.extend.text.LineExtend import LineExtend
from pdf2docx.text.Lines import Lines


class LinesExtend(ElementCollection):
    def __init__(self, lines: Lines):
        super().__init__(parent=lines._parent)
        self.lines = lines
        for line in self.lines:
            self.append(LineExtend(line))

    @property
    def image_spans(self):
        return [span for line in self for span in line.image_spans]

    def merge(self, other: LinesExtend):
        for line in other.lines:
            self.append(LineExtend(line))
    
    @property
    def is_catalog(self):
        return any([line.is_catalog for line in self.lines])
