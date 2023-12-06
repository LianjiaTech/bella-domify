from pdf2docx.common.Collection import ElementCollection
from pdf2docx.extend.text.LineExtend import LineExtend
from pdf2docx.page import Page
from pdf2docx.page.Pages import Pages
from pdf2docx.text.Lines import Lines


class LinesExtend(ElementCollection):
    def __init__(self, lines: Lines):
        super().__init__(parent=lines._parent)
        self.lines = lines
        for line in self.lines:
            self.append(LineExtend(line))

