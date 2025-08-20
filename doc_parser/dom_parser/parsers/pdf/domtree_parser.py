from __future__ import annotations

import concurrent.futures
import warnings
from typing import List, Optional, Set

from doc_parser.context import run_with_context_in_thread
from doc_parser.dom_parser.domtree.domtree import DomTree, DomTreeModel, Node
from doc_parser.dom_parser.parsers.pdf.extend.page.PagesExtend import PagesExtend
from doc_parser.dom_parser.parsers.pdf.extend.common.BlockExtend import BlockExtend

class PDFDomTreeParser:
    def __init__(self, pages: PagesExtend, debug_file=None, fitz_doc=None, *, priority=0):
        self.domtree = DomTree()
        self.elements = []
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

    def judge_title_by_child(self, parent_node):
        # 非叶子节点、文字节点、且非目录 则判定为Title
        if (not parent_node.is_root
                and parent_node.element.is_text_block
                and not parent_node.element.is_catalog
                and len(parent_node.element.text) < 25):
            parent_node.element.is_title = 1


    def add_image_data(self):
        # 构建树结构件前，先把图片的s3链接附上
        tasks_to_process = []
        for (element, page, debug_page) in self.elements:
            if element.is_image_block:
                tasks_to_process.append(element)
        # 多进程获取S3链接
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            for text_block_extend in tasks_to_process:
                # 使用run_with_context_in_thread函数来确保在正确的上下文中运行
                runner = run_with_context_in_thread(text_block_extend.image_handler)
                # 这将允许在多线程环境中使用上下文中的配置和资源
                executor.submit(runner)

    def parse(self, **settings):
        # 初始化
        stack_path: List[Node] = [self.domtree.root]
        prev_text_node: Optional[Node] = None
        searched_block: Set[BlockExtend] = set()

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
                    self.node_dict[element.refed_blocks[0]].add_child(node)
                    caption_node = Node(element.caption_block, page, debug_page)
                    self.node_dict[element.refed_blocks[0]].add_child(caption_node)
                    # 添加table caption为已搜索过的块，避免重复搜索
                    searched_block.add(element.caption_block)
                elif prev_text_node:
                    prev_text_node.add_child(node)
                    self.judge_title_by_child(prev_text_node)
                    # todo 这部分依赖title识别要准确，之后加
                    # if prev_text_node.element.block.list_type() or prev_text_node.element.is_title:
                    #     prev_text_node.add_child(node)
                    # else:
                    #     prev_text_node.add_brother(node)
                else:
                    self.domtree.root.add_child(node)
                continue
            # 处理图片块
            if element.is_image_block:
                image_span = element.lines.image_spans[0]
                if image_span.refed_blocks and image_span.refed_blocks[0] in self.node_dict and image_span.caption_block not in searched_block:
                    # 如果是图片，且有引用, 则添加到首个引用块
                    self.node_dict[image_span.refed_blocks[0]].add_child(node)
                    caption_node = Node(image_span.caption_block, page, debug_page)
                    self.node_dict[image_span.refed_blocks[0]].add_child(caption_node)
                    searched_block.add(image_span.caption_block)
                elif prev_text_node:
                    prev_text_node.add_child(node)
                    self.judge_title_by_child(prev_text_node)
                    # if prev_text_node.element.block.list_type() or prev_text_node.element.is_title:
                    #     prev_text_node.add_child(node)
                    # else:
                    #     prev_text_node.add_brother(node)
                else:
                    self.domtree.root.add_child(node)
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
                    parent_node.add_child(node)
                    # 非叶子节点、文字节点、且非目录 则判定为Title
                    self.judge_title_by_child(parent_node)
                    # 依赖层级，判定目录
                    node.identify_catalog_by_mulu()
                    node.identify_catalog_by_father(parent_node)

                    # 压栈
                    stack_path.append(node)
                    prev_text_node = node
                    break
                else:
                    stack_path.pop()
        self.domtree.generate_markdown()

        print("\n【文件结构树】\n")
        self.domtree.print_tree()

        # 返回DomTreeModel实例
        return DomTreeModel(dom_tree=self.domtree)