import concurrent.futures
import copy
import logging
import math
import time
from functools import partial
from typing import Optional

import openai
import textdistance

from pdf2docx.dom_tree.domtree import DomTree, Node
from pdf2docx.extend.llm.faq_extract import faq_extract, FAQ
from pdf2docx.extend.page.PagesExtend import PagesExtend
from pdf2docx.extend.text.TextBlockExtend import TextBlockExtend
from pdf2docx.text.TextBlock import TextBlock
from server.context import user_context


class FAQ_LLM_DomTree(DomTree):
    PROMPT = """
    你将得到从一个pdf文件的某一页提取出的文字内容
    判断一下内容是否属于FAQ文档，如果是，输出:True，否则输出:False
    ==================
    {page_content}
    """

    def __init__(self, pages: PagesExtend, debug_file=None):
        super().__init__(pages, debug_file, priority=2)

    def is_appropriate(self) -> bool:
        sample_result = self.extract_text_average_sample()
        # 多次采样判断
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 提交每个接口调用任务到线程池，并得到一个Future对象列表
            vote_res = list(executor.map(partial(self._is_faq, user=user_context.get()), sample_result))
            # 选择票数最多的结果
            is_faq_doc = vote_res.count(False) <= 2
            print(f"\n【是否按FAQ文档解析】{is_faq_doc}\n")
            return is_faq_doc

    def _is_faq(self, page_content: str, *, model="gpt-4o", user: str = "") -> bool:
        prompt = self.__class__.PROMPT.format(page_content=page_content)
        max_retry = 5
        response = None
        while max_retry > 0 and response is None:
            try:
                response = openai.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.001,
                    top_p=0.01,
                    model=model,
                    user=user
                )
            except openai.RateLimitError:
                max_retry -= 1
                time.sleep(10)
            except Exception as e:
                logging.error("openai chat error: %s", e)
                break
        if response is None:
            return False
        is_faq = response.choices[0].message.content
        logging.info("判断是否为FAQ文档: %s", is_faq)
        return is_faq == "True" or is_faq == "true"

    def parse(self, **settings):
        text_blocks = self.extract_text_block()
        inputs_texts = ["\n".join(blocks) for blocks in text_blocks]
        logging.info("start faq extract")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # 提交每个接口调用任务到线程池，并得到一个Future对象列表
            faqs = list(executor.map(partial(faq_extract, user=user_context.get()), inputs_texts))
        logging.info("end faq extract")
        qa_pair = []
        [qa_pair.extend(faq) for faq in faqs if faq]

        merged = self._merge_qa_pair(qa_pair)
        logging.info("merge end")
        for index, qa in enumerate(merged, start=1):
            # 将当前节点挂载到根节点下
            node = self._construct_qa_node(qa, index)
            node.order_num_str = str(index)
            self.root.add_child(node)

    def _construct_qa_node(self, qa: FAQ, index) -> Node:
        q_block = self._construct_text_block(qa.Q, "Q")
        a_block = self._construct_text_block(qa.A, "A")
        q_node = Node(q_block, None, None)
        q_node.order_num_str = str(index) + ".1"
        a_node = Node(a_block, None, None)
        a_node.order_num_str = str(index) + ".2"
        qa_node = Node(None, None, None)
        qa_node.add_child(q_node)
        qa_node.add_child(a_node)
        return qa_node

    def _construct_text_block(self, text: Optional[str], qa_type: str) -> TextBlockExtend:
        spans = [{'text': text, 'bbox': [1, 2, 3, 4]}]
        lines = [{'spans': spans, 'bbox': [1, 2, 3, 4]}]
        raws = {'lines': lines}
        text_block = TextBlock(raws)
        return TextBlockExtend(text_block, metadata={'qa_type': qa_type})

    def _merge_qa_pair(self, faqs: list[FAQ]) -> list[FAQ]:
        q2_dict = {}
        a2_dict = {}
        qa_pair = []
        similarity_threhold = 0.85
        for qa in faqs:
            if qa.A is None or qa.Q is None:
                continue
            q_similarity = {q: textdistance.Levenshtein().normalized_similarity(q, qa.Q) for q in q2_dict.keys()}
            if q_similarity:
                most_similarity_q = max(q_similarity.items(), key=lambda x: x[1])
                if most_similarity_q[1] > similarity_threhold:
                    similarity_qa = q2_dict[most_similarity_q[0]]
                    if not (qa.A in similarity_qa.A or similarity_qa.A in qa.A):
                        continue
                    if len(similarity_qa.A) >= len(qa.A):  # 相同Q，保留A更长的提取项
                        continue
                    else:
                        if similarity_qa in qa_pair:
                            qa_pair.remove(similarity_qa)  # 保存当前qa

            a_similarity = {a: textdistance.Levenshtein().normalized_similarity(a, qa.A) for a in a2_dict.keys()}
            if a_similarity:
                most_similarity_a = max(a_similarity.items(), key=lambda x: x[1])
                if most_similarity_a[1] > similarity_threhold:
                    similarity_qa = a2_dict[most_similarity_a[0]]
                    if not (qa.Q in similarity_qa.Q or similarity_qa.Q in qa.Q):
                        continue
                    if len(similarity_qa.Q) >= len(qa.Q):  # 相同A，保留Q更长的提取项
                        continue
                    else:
                        if similarity_qa in qa_pair:
                            qa_pair.remove(similarity_qa)  # 保存当前qa
            qa_pair.append(qa)  # 添加当前qa
            a2_dict[qa.A] = qa
            q2_dict[qa.Q] = qa
        return qa_pair

    def extract_text_average_sample(self):
        """
        抽样页数随总页数变化 示例：
        page_count: 2
        piece_list: [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]

        page_count: 6
        piece_list: [0, 0, 1, 1, 2, 3, 3, 4, 4, 5]

        page_count: 10
        piece_list: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        page_count: 20
        piece_list: [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
        """
        page_count = len(self.debug_file)
        # 抽样次数
        piece_num = 10
        piece = page_count / piece_num
        piece_list = [math.floor(piece * i) for i in range(piece_num)]
        # 抽样结果
        sample_result = []

        for page_num in piece_list:
            page = self.debug_file.load_page(page_num)  # 加载页面
            text = page.get_text()  # 提取文字
            sample_result.append(text)
        return sample_result

    def extract_text_block(self) -> list[list[str]]:
        searched_block = set()
        prev_page = None
        text_blocks = []
        page_text_blocks = []

        for (ele, page, debug_page) in self.elements:
            element = copy.deepcopy(ele)
            if page != prev_page:
                start_new_page = True
            else:
                start_new_page = False
            prev_page = page
            if start_new_page:
                if page_text_blocks:
                    text_blocks.append(page_text_blocks)
                page_text_blocks = []

            if element in searched_block:
                continue
            searched_block.add(element)

            if element.is_table_block:
                cur_talbe = element
                while cur_talbe.next_continuous_table:
                    next_table = cur_talbe.next_continuous_table
                    searched_block.add(next_table)
                    element.merge(next_table)
                    cur_talbe = next_table
                table_text = "\n".join('\t'.join(cell for cell in row if cell) for row in element.text)
                page_text_blocks.append(table_text)
            elif element.is_image_block:
                continue
            elif not element.is_text_block:
                continue
            else:
                cur_paragraph = element
                while cur_paragraph.next_continuous_paragraph:
                    # 合并连续的段落
                    next_paragraph = cur_paragraph.next_continuous_paragraph
                    searched_block.add(next_paragraph)
                    element.merge(next_paragraph)
                    cur_paragraph = next_paragraph
                page_text_blocks.append(element.text)
        text_blocks.append(page_text_blocks)
        return self.page_overlap(text_blocks)

    def page_overlap(self, text_blocks: list[list[str]], overlap_blocks=3) -> list[list[str]]:
        # 在text_blocks前后各插入一个空列表
        padding_blocks = [[]]
        padding_blocks.extend(text_blocks)
        padding_blocks.append([])
        blocks = []

        for prev_page_block, cur_page_block, next_page_block in zip(padding_blocks, padding_blocks[1:],
                                                                    padding_blocks[2:]):
            prev_part = prev_page_block[-overlap_blocks:] if prev_page_block else []
            cur_page_part = [block for block in cur_page_block]
            next_page_part = next_page_block[:overlap_blocks] if next_page_block else []
            blocks.append(prev_part + cur_page_part + next_page_part)
        return blocks
