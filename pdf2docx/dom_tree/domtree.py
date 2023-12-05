from typing import List, Optional

from pdf2docx.common.Block import Block
from pdf2docx.page import Page
from pdf2docx.text.TextSpan import TextSpan


class Node:
    def __init__(self, element: Optional[Block], is_root=False):
        self.element = element
        self.child = []
        self.is_root = is_root

    def is_child_of(self, node):
        """Check if self is a child of node"""
        if node.is_root:
            return True
        # 考虑基于字体、缩进等判断父子关系
        return self.judge_by_text_font(node)

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

    def add_child(self, node):
        self.child.append(node)


class DomTree:
    def __init__(self, page: Page, elements: List[Block] = None):
        self.root = Node(None, is_root=True)
        self.elements = []
        if elements:
            self.elements.extend(elements)
        else:
            for section in page.sections:
                for column in section:
                    for block in column.blocks:
                        self.elements.append(block)

    def parse(self):
        stack_path: List[Node] = [self.root]

        for element in self.elements:
            if not element.is_text_block:
                # 先分析text block
                continue
            node = Node(element)
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
        self.print_tree()

    def print_tree(self):
        self._print_tree(self.root, 0)

    def _print_tree(self, node, level):
        if node.element:
            # level为缩进层数
            print("    " * level, node.element.text)
        for child in node.child:
            self._print_tree(child, level + 1)
