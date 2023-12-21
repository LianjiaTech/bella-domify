from __future__ import annotations
from typing import List, Optional, Union, Any

from pydantic import BaseModel, computed_field, PrivateAttr

from pdf2docx.common.share import rgb_component_from_name
from pdf2docx.extend.common.BlockExtend import BlockExtend
from pdf2docx.extend.page.PageExtend import PageExtend
from pdf2docx.extend.page.PagesExtend import PagesExtend
from pdf2docx.extend.table.TableBlockExtend import TableBlockExtend, TableBlockModel
from pdf2docx.extend.text.TextBlockExtend import TextBlockExtend, TextBlockModel
from pdf2docx.text.TextSpan import TextSpan


class NodeModel(BaseModel):
    _node: Node = PrivateAttr()

    def __init__(self, node):
        super().__init__()
        self._node = node

    class Config:
        arbitrary_types_allowed = True

    @computed_field
    @property
    def child(self) -> List[NodeModel]:
        child_model = []
        for child in self._node.child:
            child_model.append(NodeModel(node=child))
        return child_model

    @computed_field
    @property
    def order_num(self) -> Optional[str]:
        return self._node.order_num_str

    @computed_field
    @property
    def element(self) -> Union[TextBlockModel, TableBlockModel, None]:
        if isinstance(self._node.element, TextBlockExtend):
            return TextBlockModel(block=self._node.element)
        elif isinstance(self._node.element, TableBlockExtend):
            return TableBlockModel(block=self._node.element, order_num=self.order_num)
        else:
            return None


class Node:
    def __init__(self, element: Optional[BlockExtend], page: Optional[PageExtend], debug_page, is_root=False):
        self.element = element
        self.child = []
        self.parent = None
        self.is_root = is_root
        self.page = page
        self.debug_page = debug_page
        self.order_num_str = None  # 当前元素的有序列表序号 1.1, 1.2.1

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
        cur_span_bold = bool(cur_span.flags & 2 ** 4) or cur_span.pseudo_bold
        node_span_bold = bool(node_span.flags & 2 ** 4) or node_span.pseudo_bold
        if isinstance(cur_span, TextSpan) and isinstance(node_span, TextSpan):
            if cur_span.size < node_span.size:
                return True
            elif cur_span.size <= node_span.size and (not cur_span_bold) and node_span_bold:
                # 如果当前span的字体大小小于等于父节点的字体大小，且当前span不是粗体，父节点是粗体，则认为当前span是父节点的子节点
                return True
        return False

    def judge_by_order_list(self, node):
        return self.element.block.list_type() \
            and self.element.block.list_type() != node.element.block.list_type()

    def add_child(self, node: Node):
        self.child.append(node)
        node.parent = self

    def union_bbox(self):
        if not self.child:
            return
        for child in self.child:
            child.union_bbox()
        [self.element.union_bbox(child.element) for child in self.child]

    def plot(self):
        if self.element and self.debug_page:
            self.element.block.extend_plot(self.debug_page)
            blue = rgb_component_from_name('blue')
            yellow = rgb_component_from_name('yellow')
            self.debug_page.draw_rect((self.element.block.bbox.x0, self.element.block.bbox.y0 - 8,
                                       self.element.block.bbox.x0 + 50, self.element.block.bbox.y0), color=blue,
                                      fill=blue)
            self.debug_page.insert_text((self.element.bbox.x0, self.element.bbox.y0),
                                        self.order_num_str, color=yellow)


class DomTreeModel(BaseModel):
    _dom_tree: DomTree = PrivateAttr()

    def __init__(self, dom_tree, **data: Any):
        super().__init__(**data)
        self._dom_tree = dom_tree

    class Config:
        arbitrary_types_allowed = True

    @computed_field
    @property
    def root(self) -> NodeModel:
        return NodeModel(node=self._dom_tree.root)


class DomTree:

    def __init__(self, pages: PagesExtend, debug_file=None):
        self.root = Node(None, None, None, is_root=True)
        self.elements = []
        self.node_dict = {}  # element->node
        self.debug_file = debug_file
        debug_pages = [page for page in debug_file.pages()] if debug_file else None
        for index, page in enumerate(pages):
            for section in page.sections:
                for column in section:
                    for block in column.blocks:
                        # 跳过页眉页脚
                        if block.block.is_header or block.block.is_footer:
                            continue
                        if debug_pages:
                            self.elements.append((block, page, debug_pages[index]))
                        else:
                            self.elements.append((block, page, None))

    def get_text_block(self):
        return self._get_text_block(self.root)

    def _get_text_block(self, node: Node) -> list[str]:
        texts = []
        if node.element and node.element.is_text_block:
            texts.append(node.element.text)
        for child in node.child:
            texts.extend(self._get_text_block(child))
        return texts

    def parse(self):
        stack_path: List[Node] = [self.root]
        prev_text_node: Optional[Node] = None
        searched_block = set()

        for (element, page, debug_page) in self.elements:
            if element in searched_block:
                continue
            node = Node(element, page, debug_page)
            searched_block.add(element)
            self.node_dict[element] = node
            if element.is_table_block:
                cur_talbe = element
                while cur_talbe.next_continuous_table:
                    next_table = cur_talbe.next_continuous_table
                    searched_block.add(next_table)
                    element.merge(next_table)
                    cur_talbe = next_table

                if element.refed_blocks:
                    # 如果是表格，且有引用, 则添加到首个引用块
                    self.node_dict[element.refed_blocks[0]].add_child(node)
                    caption_node = Node(element.caption_block, page, debug_page)
                    self.node_dict[element.refed_blocks[0]].add_child(caption_node)
                    # 添加table caption为已搜索过的块，避免重复搜索
                    searched_block.add(element.caption_block)
                elif prev_text_node:
                    prev_text_node.add_child(node)
                else:
                    self.root.add_child(node)
                continue
            if element.is_image_block:
                image_span = element.lines.image_spans[0]
                if image_span.refed_blocks:
                    # 如果是图片，且有引用, 则添加到首个引用块
                    self.node_dict[image_span.refed_blocks[0]].add_child(node)
                    caption_node = Node(image_span.caption_block, page, debug_page)
                    self.node_dict[image_span.refed_blocks[0]].add_child(caption_node)
                    searched_block.add(image_span.caption_block)
                elif prev_text_node:
                    prev_text_node.add_child(node)
                else:
                    self.root.add_child(node)
                continue
            if not element.is_text_block:
                # 先分析text block
                continue

            cur_paragraph = node.element
            while cur_paragraph.next_continuous_paragraph:
                next_paragraph = cur_paragraph.next_continuous_paragraph
                searched_block.add(next_paragraph)
                node.element.merge(next_paragraph)
                cur_paragraph = next_paragraph
            while True:
                if node.is_child_of(stack_path[-1]):
                    parent_node = stack_path[-1]

                    # 如果是列表，且和上一节点不是同一类型列表，则尝试找到上一组相同类型的列表
                    if node.element.block.list_type():
                        same_node = node.recursion_find_same_list_type_node(stack_path[-1])
                        if same_node:
                            parent_node = same_node.parent
                            stack_path.pop()
                            stack_path.append(parent_node)

                    # 增加子节点
                    parent_node.add_child(node)
                    # 压栈
                    stack_path.append(node)
                    prev_text_node = node
                    break
                else:
                    stack_path.pop()
        print("parse finished")
        self.print_tree()

    def union_bbox(self):
        for child in self.root.child:
            child.union_bbox()

    def print_tree(self):
        self._print_tree(self.root, 0, "", 1)

    def _print_tree(self, node, level, parent_order_str, order):
        cur_order_str = parent_order_str
        if node.element:
            # level为缩进层数
            cur_order_str = f"{parent_order_str}.{order}" if parent_order_str else f"{order}"
            node.order_num_str = cur_order_str  # 记录其有效列表序号
            if node.debug_page:
                node.plot()
            print("    " * level + cur_order_str, node.element.text)
        for i, child in enumerate(node.child, start=1):
            self._print_tree(child, level + 1, cur_order_str, i)
