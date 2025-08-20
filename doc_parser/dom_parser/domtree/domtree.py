from __future__ import annotations

import re
from typing import List, Optional
from typing import Union, Any

from pydantic import BaseModel, computed_field, PrivateAttr

from doc_parser.dom_parser.parsers.pdf.common.share import rgb_component_from_name
from doc_parser.dom_parser.parsers.pdf.extend.common.BlockExtend import BlockExtend
from doc_parser.dom_parser.parsers.pdf.extend.page.PageExtend import PageExtend
from doc_parser.dom_parser.parsers.pdf.extend.table.RowsExtend import RowsExtend
from doc_parser.dom_parser.parsers.pdf.extend.table.TableBlockExtend import TableBlockExtend, TableBlockModel
from doc_parser.dom_parser.parsers.pdf.extend.text.TextBlockExtend import TextBlockExtend, TextBlockModel
from doc_parser.dom_parser.parsers.pdf.text.TextSpan import TextSpan



class NodeModel(BaseModel):
    _node: Node = PrivateAttr()

    def __init__(self, node):
        super().__init__()
        self._node = node

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

    def identify_catalog_by_mulu(self):
        if "目录" in self.element.text.replace(' ', ''):
            self.element.is_catalog = True

    def identify_catalog_by_father(self, father_node):
        if father_node.element and father_node.element.is_catalog:
            self.element.is_catalog = True

    def is_child_of(self, node):
        """Check if self is a child of node"""
        if node.is_root:
            return True

        # 目录的子节点认定
        if not self.judge_by_catalog(node):
            return False

        # Title节点不能是普通text的子节点，只能是另一个Title的子节点
        if not self.judge_by_title(node):
            return False

        # 考虑基于字体、缩进等判断父子关系；
        if self.judge_by_text_font(node):
            return True

        # 如果是列表，则判断是否是父节点的子节点
        if not self.judge_by_order_list(node):
            return False

        return True

        # # ①考虑基于字体、缩进等判断父子关系；②如果是列表，则判断是否是父节点的子节点
        # return self.judge_by_text_font(node) or self.judge_by_order_list(node)

    def judge_by_title(self, node):
        # Title节点，只能是Title的子节点，不能是text的子节点
        cur_span_is_title = self.element.is_title
        node_span_is_title = node.element.is_title
        if cur_span_is_title and not node_span_is_title:
            return False

        return True

    def judge_by_catalog(self, node):
        # 特殊条件：目录节点下只能包含目录项
        pattern = re.compile(r'(.)\1{9,}\d+')

        # 目录的子节点，只能是目录项
        # 第一种目录项：“文字......x”
        # 第二种目录项：带链接
        if "目录" in node.element.text.replace(' ', ''):
            if not pattern.search(self.element.text.strip().replace(' ', '')) and not self.element.lines.get_if_first_line_link():
                return False

        # # 目录项和目录项不能作为父子节点  !!提醒，此项不能加，因为目录也是有层级结构的，目录项之间也有父子关系
        # if pattern.search(self.element.text.strip().replace(' ', '')) and pattern.search(node.element.text.strip().replace(' ', '')):
        #     return False

        return True

    def judge_by_text_font(self, node):
        cur_span = self.element.lines[0].spans[0]
        node_span = node.element.lines[0].spans[0]
        if (not isinstance(cur_span, TextSpan)) or (not isinstance(node_span, TextSpan)):
            return False

        cur_font, cur_size, cur_bold = self.element.lines.get_font_size_bold()
        node_font, node_size, node_bold = node.element.lines.get_font_size_bold()

        if isinstance(cur_span, TextSpan) and isinstance(node_span, TextSpan):
            if cur_size < node_size:
                return True
            elif cur_size <= node_size and (not cur_bold) and node_bold:
                # 如果当前span的字体大小小于等于父节点的字体大小，且当前span不是粗体，父节点是粗体，则认为当前span是父节点的子节点
                return True
        return False

    def judge_by_order_list(self, node):
        """
        list层级相同不能认定为父节点
        text也可视作一种层级

        普通文本不可以作为普通文本的子节点（应为兄弟）
        (1)不可以作为（2）的子节点（应为兄弟）

        """
        return self.element.block.list_type() != node.element.block.list_type()

    # 找到上一组和当前列表相同类型的节点
    def recursion_find_same_list_type_node(self, node):
        # 如果对照节点是相同的list类型，则找到并返回
        if self.same_list_type_node(node):
            return node
        # 如果对照节点有父节点，且父节点不是root，则递归对照父节点
        elif node.parent and not node.parent.is_root:
            return self.recursion_find_same_list_type_node(node.parent)
        return None

    def same_list_type_node(self, node):
        return not node.is_root and self.element.block.list_type() == node.element.block.list_type()

    def add_child(self, node: Node):
        self.child.append(node)
        node.parent = self

    def add_brother(self, node: Node):
        self.parent.child.append(node)
        node.parent = self.parent

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
                                       self.element.block.bbox.x0 + len(self.order_num_str) * 5.5, self.element.block.bbox.y0), color=blue,
                                      fill=blue)
            self.debug_page.insert_text((self.element.bbox.x0, self.element.bbox.y0),
                                        self.order_num_str, color=yellow)


class DomTreeModel(BaseModel):
    _dom_tree: DomTree = PrivateAttr()

    def __init__(self, dom_tree: DomTree, **data: Any):
        super().__init__(**data)
        self._dom_tree = dom_tree

    @computed_field
    @property
    def root(self) -> NodeModel:
        return NodeModel(self._dom_tree.root)

    def to_markdown(self) -> str:
        """
        将DOM树转换为Markdown格式的字符串

        Returns:
            str: Markdown格式的字符串
        """
        # 调用DomTree的to_markdown方法
        return self._dom_tree.to_markdown()

class DomTree:

    def __init__(self):
        self.root = Node(None, None, None, is_root=True)
        self.markdown_res = ""

    def print_tree(self):
        self._print_tree(self.root, 0, "", 1)

    def to_markdown(self) -> str:
        """
        将DOM树转换为Markdown格式的字符串

        Returns:
            str: Markdown格式的字符串
        """
        # 使用局部变量存储Markdown内容
        markdown_res = ""

        # 定义内部函数来生成Markdown
        def _generate_markdown_local(node, level, parent_order_str, order, low_than_text=0):
            nonlocal markdown_res
            cur_order_str = parent_order_str
            child_low_than_text = 0
            if node.element:
                cur_order_str = f"{parent_order_str}.{order}" if parent_order_str else f"{order}"
                node.order_num_str = cur_order_str

                # 根据不同的layout_type生成Markdown
                if node.element.layout_type == "Figure" and node.element.image_link:
                    markdown_res += f"![Figure]({node.element.image_link})\n\n"
                    md_ocr_res = self.convert_to_markdown_quote(node.element.image_ocr_result)
                    markdown_res += f"{md_ocr_res}\n\n"
                elif node.element.layout_type == "Table":
                    table_md = self.list_to_html_table(node.element._rows)
                    if node.element.next_continuous_table:
                        continuous_table_md = self.get_continuous_table_markdown(node.element.next_continuous_table)
                        table_md += continuous_table_md
                    markdown_res += f"{table_md}\n\n"

                elif (level <= 6  # 标题必须小于等于6级
                      and (node.element.layout_type in ["Title"]  # 认定为Title 或者 父节点非text的List
                           or (node.element.layout_type in ["List"] and not low_than_text))):
                    # Title只能识别6级，大于6级的按普通文本处理
                    markdown_res += '#' * level + f" {node.element.text}\n\n"
                elif node.element.layout_type in ["Title"]:
                    markdown_res += f"{node.element.text}\n\n"
                elif node.element.layout_type in ["Text"]:
                    markdown_res += f"{node.element.text}\n\n"
                    child_low_than_text = low_than_text + 1  # Text节点的子节点标记
                elif node.element.layout_type in ["List"]:
                    markdown_res += '\t' * (low_than_text - 1) + f"- {node.element.text}\n\n"
                # Formula、Catalog、Code等元素的处理
                else:
                    markdown_res += f"{node.element.text}\n\n"

            for i, child in enumerate(node.child, start=1):
                _generate_markdown_local(child, level + 1, cur_order_str, i, child_low_than_text)

        # 调用内部函数生成Markdown
        _generate_markdown_local(self.root, 0, "", 1)

        # 返回生成的Markdown内容
        return markdown_res

    def _print_tree(self, node, level, parent_order_str, order):
        cur_order_str = parent_order_str
        if node.element:
            # level为缩进层数
            cur_order_str = f"{parent_order_str}.{order}" if parent_order_str else f"{order}"
            node.order_num_str = cur_order_str  # 记录其有效列表序号
            if node.debug_page:
                node.plot()
            try:
                # 尝试打印节点文本
                print("    " * level + cur_order_str, node.element.text)
            except UnicodeEncodeError:
                print("\n【节点含特殊字符】" + cur_order_str)
                print("    " * level + cur_order_str, "")

        for i, child in enumerate(node.child, start=1):
            self._print_tree(child, level + 1, cur_order_str, i)

    def generate_markdown(self):
        self._generate_markdown(self.root, 0, "", 1)

    def _generate_markdown(self, node, level, parent_order_str, order, low_than_text=0):
        cur_order_str = parent_order_str
        child_low_than_text = 0
        if node.element:
            cur_order_str = f"{parent_order_str}.{order}" if parent_order_str else f"{order}"
            node.order_num_str = cur_order_str

            # 根据不同的layout_type生成Markdown
            if node.element.layout_type == "Figure" and node.element.image_link:
                self.markdown_res += f"![Figure]({node.element.image_link})\n\n"
                md_ocr_res = self.convert_to_markdown_quote(node.element.image_ocr_result)
                self.markdown_res += f"{md_ocr_res}\n\n"
            elif node.element.layout_type == "Table":
                table_md = self.list_to_html_table(node.element._rows)
                if node.element.next_continuous_table:
                    continuous_table_md = self.get_continuous_table_markdown(node.element.next_continuous_table)
                    table_md += continuous_table_md
                self.markdown_res += f"{table_md}\n\n"

            elif (level <= 6  # 标题必须小于等于6级
                  and (node.element.layout_type in ["Title"]  # 认定为Title 或者 父节点非text的List
                       or (node.element.layout_type in ["List"] and not low_than_text))):
                # Title只能识别6级，大于6级的按普通文本处理
                self.markdown_res += '#' * level + f" {node.element.text}\n\n"
            elif node.element.layout_type in ["Title"]:
                self.markdown_res += f"{node.element.text}\n\n"
            elif node.element.layout_type in ["Text"]:
                self.markdown_res += f"{node.element.text}\n\n"
                child_low_than_text = low_than_text + 1  # Text节点的子节点标记
            elif node.element.layout_type in ["List"]:
                self.markdown_res += '\t' * (low_than_text - 1) + f"- {node.element.text}\n\n"
            # Formula、Catalog、Code等元素的处理
            else:
                self.markdown_res += f"{node.element.text}\n\n"

        for i, child in enumerate(node.child, start=1):
            self._generate_markdown(child, level + 1, cur_order_str, i, child_low_than_text)

    def convert_to_markdown_quote(self, text):
        lines = text.split('\n')
        quoted_lines = ['> ' + line for line in lines]
        return '\n'.join(quoted_lines)

    def list_to_html_table(self, rows: RowsExtend):
        html_text = "<table>"

        for row in rows:
            html_text += "<tr>"
            for cell in row._cells:
                rowspan = cell.end_row - cell.start_row + 1
                colspan = cell.end_col - cell.start_col + 1
                html_text += f"<td rowspan='{rowspan}' colspan='{colspan}'>{cell.text}</td>"
            html_text += "</tr>"
        html_text += "</table>"
        return html_text

    def get_continuous_table_markdown(self, element: TableBlockExtend):
        markdown_content = self.list_to_html_table(element._rows)
        if element.next_continuous_table:
            continuous_table_md = self.get_continuous_table_markdown(element.next_continuous_table)
            markdown_content += continuous_table_md

        return markdown_content