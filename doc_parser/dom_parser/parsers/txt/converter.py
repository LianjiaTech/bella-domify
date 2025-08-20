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
        try:
            content = self.stream.decode(decode_type)
        # 解析失败，尝试使用gbk编码进行解析
        except:
            content = self.stream.decode('gbk')

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
