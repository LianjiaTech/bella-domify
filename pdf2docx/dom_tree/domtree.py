from __future__ import annotations

import concurrent.futures
import re
from typing import List, Optional
from typing import Union, Any

from pydantic import BaseModel, computed_field, PrivateAttr

from pdf2docx.common.share import rgb_component_from_name
from pdf2docx.extend.common.BlockExtend import BlockExtend
from pdf2docx.extend.page.PageExtend import PageExtend
from pdf2docx.extend.page.PagesExtend import PagesExtend
from pdf2docx.extend.table import RowsExtend
from pdf2docx.extend.table.TableBlockExtend import TableBlockExtend, TableBlockModel
from pdf2docx.extend.text.TextBlockExtend import TextBlockExtend, TextBlockModel
from pdf2docx.text.TextSpan import TextSpan
from server.context import user_context


def judge_title_by_child(parent_node):
    # 非叶子节点、文字节点、且非目录 则判定为Title
    if (not parent_node.is_root
            and parent_node.element.is_text_block
            and not parent_node.element.is_catalog
            and len(parent_node.element.text) < 25):
        parent_node.element.is_title = 1


class NodeModel(BaseModel):
    _node: Node = PrivateAttr()

    def __init__(self, node):
        super().__init__()
        self._node = node

    @computed_field
    @property
    def children(self) -> List[NodeModel]:
        child_model = []
        for child in self._node.children:
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
        self.children = []
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

    def add_children(self, node: Node):
        self.children.append(node)
        node.parent = self

    def add_brother(self, node: Node):
        self.parent.children.append(node)
        node.parent = self.parent

    def union_bbox(self):
        if not self.children:
            return
        for child in self.children:
            child.union_bbox()
        [self.element.union_bbox(child.element) for child in self.children]

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

    def __init__(self, dom_tree, **data: Any):
        super().__init__(**data)
        self._dom_tree = dom_tree

    @computed_field
    @property
    def root(self) -> NodeModel:
        return NodeModel(node=self._dom_tree.root)


class DomTree:
    def __init__(self, pages: PagesExtend, debug_file=None, fitz_doc=None, *, priority=0):
        self.root = Node(None, None, None, is_root=True)
        self.elements = []
        self.markdown_res = ""
        self.node_dict = {}  # element->node
        self.debug_file = debug_file
        self._fitz_doc = fitz_doc
        self._priority = priority
        debug_pages = [page for page in debug_file.pages()] if debug_file else None
        for index, page in enumerate(pages):
            for section in page.sections:
                for column in section:
                    for block in column.blocks:
                        # 跳过页眉页脚
                        if block.block.is_header or block.block.is_footer:
                            continue
                        block.page_num = [page.page.id]
                        if debug_pages:
                            self.elements.append((block, page, debug_pages[index]))
                        else:
                            self.elements.append((block, page, None))

    def is_appropriate(self) -> bool:
        """
        当前DomTree解析是否适用于当前文档
        """
        return True

    @property
    def priority(self) -> int:
        """
        如果存在多个DomTree可用，优先级高的会被优先选中
        """
        return self._priority

    def get_text_block(self):
        return self._get_text_block(self.root)

    def _get_text_block(self, node: Node) -> list[str]:
        texts = []
        if node.element and node.element.is_text_block:
            texts.append(node.element.text)
        for child in node.children:
            texts.extend(self._get_text_block(child))
        return texts

    def add_image_data(self):
        # 构建树结构件前，先把图片的s3链接附上
        tasks_to_process = []
        for (element, page, debug_page) in self.elements:
            if element.is_image_block:
                tasks_to_process.append(element)
        # 多进程获取S3链接
        user = user_context.get()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            executor.map(lambda text_block_extend: text_block_extend.image_handler(user),
                         tasks_to_process)

    def parse(self, **settings):

        # 初始化
        stack_path: List[Node] = [self.root]
        prev_text_node: Optional[Node] = None
        searched_block = set()

        # 添加图片s3链接
        self.add_image_data()

        # 遍历解析
        for (element, page, debug_page) in self.elements:
            if element in searched_block:
                continue
            node = Node(element, page, debug_page)
            searched_block.add(element)
            self.node_dict[element] = node
            # 处理表格块
            if element.is_table_block:
                cur_talbe = element
                while cur_talbe.next_continuous_table:
                    next_table = cur_talbe.next_continuous_table
                    searched_block.add(next_table)
                    element.merge(next_table)
                    cur_talbe = next_table

                if element.refed_blocks and element.refed_blocks[0] in self.node_dict and element.caption_block not in searched_block:
                    # 如果是表格，且有引用, 则添加到首个引用块
                    self.node_dict[element.refed_blocks[0]].add_children(node)
                    caption_node = Node(element.caption_block, page, debug_page)
                    self.node_dict[element.refed_blocks[0]].add_children(caption_node)
                    # 添加table caption为已搜索过的块，避免重复搜索
                    searched_block.add(element.caption_block)
                elif prev_text_node:
                    prev_text_node.add_children(node)
                    judge_title_by_child(prev_text_node)
                    # todo 这部分依赖title识别要准确，之后加
                    # if prev_text_node.element.block.list_type() or prev_text_node.element.is_title:
                    #     prev_text_node.add_child(node)
                    # else:
                    #     prev_text_node.add_brother(node)
                else:
                    self.root.add_children(node)
                continue
            # 处理图片块
            if element.is_image_block:
                image_span = element.lines.image_spans[0]
                if image_span.refed_blocks and image_span.refed_blocks[0] in self.node_dict and image_span.caption_block not in searched_block:
                    # 如果是图片，且有引用, 则添加到首个引用块
                    self.node_dict[image_span.refed_blocks[0]].add_children(node)
                    caption_node = Node(image_span.caption_block, page, debug_page)
                    self.node_dict[image_span.refed_blocks[0]].add_children(caption_node)
                    searched_block.add(image_span.caption_block)
                elif prev_text_node:
                    prev_text_node.add_children(node)
                    judge_title_by_child(prev_text_node)
                    # if prev_text_node.element.block.list_type() or prev_text_node.element.is_title:
                    #     prev_text_node.add_child(node)
                    # else:
                    #     prev_text_node.add_brother(node)
                else:
                    self.root.add_children(node)
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

            # 处理层级关系
            while True:
                if node.is_child_of(stack_path[-1]):
                    parent_node = stack_path[-1]

                    # 如果是列表，且和上一节点不是同一类型列表，则尝试找到上一组相同类型的列表
                    # if node.element.block.list_type() and not node.element.block.list_first_item():  # todo
                    if node.element.block.list_type():
                        same_node = node.recursion_find_same_list_type_node(stack_path[-1])
                        if same_node:
                            parent_node = same_node.parent
                            stack_path.pop()
                            stack_path.append(parent_node)

                    # 增加子节点
                    parent_node.add_children(node)
                    # 非叶子节点、文字节点、且非目录 则判定为Title
                    judge_title_by_child(parent_node)
                    # 依赖层级，判定目录
                    node.identify_catalog_by_mulu()
                    node.identify_catalog_by_father(parent_node)

                    # 压栈
                    stack_path.append(node)
                    prev_text_node = node
                    break
                else:
                    stack_path.pop()
        self.generate_markdown()

        print("\n【文件结构树】\n")
        self.print_tree()

    def union_bbox(self):
        for child in self.root.children:
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
            try:
                # 尝试打印节点文本
                print("    " * level + cur_order_str, node.element.text)
            except UnicodeEncodeError:
                print("\n【节点含特殊字符】" + cur_order_str)
                print("    " * level + cur_order_str, "")

        for i, child in enumerate(node.children, start=1):
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
            if node.element.layout_type == "Figure":
                self.markdown_res += f"![Figure]({node.element.image_s3_link})\n\n"
                md_ocr_res = convert_to_markdown_quote(node.element.image_ocr_result)
                self.markdown_res += f"{md_ocr_res}\n\n"
            elif node.element.layout_type == "Table":
                table_md = list_to_html_table(node.element._rows)
                if node.element.next_continuous_table:
                    continuous_table_md = get_continuous_table_markdown(node.element.next_continuous_table)
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

        for i, child in enumerate(node.children, start=1):
            self._generate_markdown(child, level + 1, cur_order_str, i, child_low_than_text)


def convert_to_markdown_quote(text):
    lines = text.split('\n')
    quoted_lines = ['> ' + line for line in lines]
    return '\n'.join(quoted_lines)


def list_to_html_table(rows: RowsExtend):
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


def get_continuous_table_markdown(element: TableBlockExtend):
    markdown_content = list_to_html_table(element._rows)
    if element.next_continuous_table:
        continuous_table_md = get_continuous_table_markdown(element.next_continuous_table)
        markdown_content += continuous_table_md

    return markdown_content
