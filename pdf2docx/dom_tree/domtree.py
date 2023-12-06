from typing import List, Optional

from pdf2docx.common.Block import Block
from pdf2docx.extend.common.BlockExtend import BlockExtend
from pdf2docx.extend.page.PageExtend import PageExtend
from pdf2docx.extend.page.PagesExtend import PagesExtend
from pdf2docx.page import Page
from pdf2docx.text.TextSpan import TextSpan


class Node:
    def __init__(self, element: Optional[BlockExtend], page: Optional[PageExtend], is_root=False):
        self.element = element
        self.child = []
        self.is_root = is_root
        self.page = page

    def is_child_of(self, node):
        """Check if self is a child of node"""
        if node.is_root:
            return True
        # ①考虑基于字体、缩进等判断父子关系；②如果是列表，则判断是否是父节点的子节点
        return self.judge_by_text_font(node) or self.judge_by_order_list(node)

    def judge_by_text_font(self, node):
        cur_span = self.element.lines[0].spans[0]
        node_span = node.element.lines[0].spans[0]
        if (not isinstance(cur_span, TextSpan)) or (not isinstance(node_span, TextSpan)):
            return False
        cur_span_bold = bool(cur_span.flags & 2 ** 4)
        node_span_bold = bool(node_span.flags & 2 ** 4)
        if isinstance(cur_span, TextSpan) and isinstance(node_span, TextSpan):
            if cur_span.size < node_span.size:
                return True
            elif cur_span.size <= node_span.size and (not cur_span_bold) and node_span_bold:
                # 如果当前span的字体大小小于等于父节点的字体大小，且当前span不是粗体，父节点是粗体，则认为当前span是父节点的子节点
                return True
        return False

    def judge_by_order_list(self, node):
        return node.element.block.list_type() and self.element.block.list_type() \
            and self.element.block.list_type() != node.element.block.list_type()

    def add_child(self, node):
        self.child.append(node)

    def union_bbox(self):
        if not self.child:
            return
        for child in self.child:
            child.union_bbox()
        [self.element.union_bbox(child.element) for child in self.child]


class DomTree:
    def __init__(self, pages: PagesExtend):
        self.root = Node(None, None, is_root=True)
        self.elements = []
        self.node_dict = {} #element->node
        for page in pages:
            for section in page.sections:
                for column in section:
                    for block in column.blocks:
                        self.elements.append((block, page))

    def parse(self):
        stack_path: List[Node] = [self.root]

        for (element, page) in self.elements:
            node = Node(element, page)
            self.node_dict[element] = node
            if element.is_table_block:
                if element.refed_blocks:
                    # 如果是表格，且有引用, 则添加到首个引用块
                    self.node_dict[element.refed_blocks[0]].add_child(node)
                else:
                    self.root.add_child(node)
                continue
            if element.is_image_block:
                image_span = element.lines.image_spans[0]
                if image_span.refed_blocks:
                    # 如果是图片，且有引用, 则添加到首个引用块
                    self.node_dict[image_span.refed_blocks[0]].add_child(node)
                else:
                    self.root.add_child(node)
                continue
            if not element.is_text_block:
                # 先分析text block
                continue
            while True:
                if node.is_child_of(stack_path[-1]):
                    # 增加子节点
                    stack_path[-1].add_child(node)
                    # 压栈
                    stack_path.append(node)
                    break
                else:
                    stack_path.pop()
        print("parse finished")
        self.union_bbox()
        self.print_tree()

    def union_bbox(self):
        for child in self.root.child:
            child.union_bbox()

    def print_tree(self):
        self._print_tree(self.root, 0)

    def _print_tree(self, node, level):
        if node.element:
            # level为缩进层数
            print("    " * level, node.element.block.text)
        for child in node.child:
            self._print_tree(child, level + 1)
