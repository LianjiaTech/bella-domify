from doc_parser.dom_parser.domtree.domtree import DomTree, Node, DomTreeModel
from doc_parser.dom_parser.parsers.base import BaseConverter
from doc_parser.dom_parser.parsers.pdf.extend.text.TextBlockExtend import TextBlockExtend
from doc_parser.dom_parser.parsers.pdf.text.TextBlock import TextBlock
from utils.general_util import detect_encoding


class TxtConverter(BaseConverter):

    def __init__(self, stream: bytes):
        self.stream = stream

    def dom_tree_parse(self, start: int = 0, end: int = None, pages: list = None, **kwargs):
        decode_type = detect_encoding(self.stream)
        encodings = [decode_type, 'gbk', 'utf-8', 'utf-16', 'latin1']

        for encoding in filter(None, encodings):
            try:
                content = self.stream.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            content = self.stream.decode('utf-8', errors='ignore')

        dom_tree = DomTree()
        # txt文件通常只有一页，所以不需要处理页码，整体作为一个block
        text_block =self._build_text_block(text=content)
        text_block_extend = TextBlockExtend(text_block=text_block)
        text_block_extend.page_num = [0]
        node = Node(text_block_extend, None, None)
        dom_tree.root.add_child(node)
        return DomTreeModel(dom_tree = dom_tree)

    def _build_text_block(self, text: str):
        """Build a TextBlockExtend from text."""
        # txt暂时只保留内容，其余元信息暂不处理，bbox是占位
        raw_lines = [{'spans': [{'text': text, 'bbox': [0, 1, 0, 1]}], 'bbox': [0, 1, 0, 1]}]
        raw_block = {'lines': raw_lines, 'bbox': [0, 1, 0, 1]}
        block = TextBlock(raw=raw_block)
        return block
