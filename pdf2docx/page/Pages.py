# -*- coding: utf-8 -*-

'''Collection of :py:class:`~pdf2docx.page.Page` instances.'''

import logging
import re
from collections import Counter

from shapely.geometry import box

from .RawPageFactory import RawPageFactory
from ..common.Collection import BaseCollection
from ..font.Fonts import Fonts
from ..shape.Shape import Stroke


class Pages(BaseCollection):
    '''A collection of ``Page``.'''

    def parse(self, fitz_doc, **settings):
        '''Analyze document structure, e.g. page section, header, footer.

        Args:
            fitz_doc (fitz.Document): ``PyMuPDF`` Document instance.
            settings (dict): Parsing parameters.
        '''
        # ---------------------------------------------
        # 0. extract fonts properties, especially line height ratio
        # ---------------------------------------------
        fonts = Fonts.extract(fitz_doc)

        # ---------------------------------------------
        # 1. extract and then clean up raw page
        # ---------------------------------------------
        pages, raw_pages = [], []
        words_found = False
        for page in self:
            if page.skip_parsing: continue

            # init and extract data from PDF
            raw_page = RawPageFactory.create(page_engine=fitz_doc[page.id], backend='PyMuPDF')
            raw_page.restore(**settings)

            # check if any words are extracted since scanned pdf may be directed
            if not words_found and raw_page.raw_text.strip():
                words_found = True

            # process blocks and shapes based on bbox
            raw_page.clean_up(**settings)

            # process font properties
            raw_page.process_font(fonts)            

            # after this step, we can get some basic properties
            # NOTE: floating images are detected when cleaning up blocks, so collect them here
            page.width = raw_page.width
            page.height = raw_page.height
            page.float_images.reset().extend(raw_page.blocks.floating_image_blocks)

            raw_pages.append(raw_page)
            pages.append(page)

        # show message if no words found
        if not words_found:
            logging.warning('Words count: 0. It might be a scanned pdf, which is not supported yet.')

        # ---------------------------------------------
        # 2. parse structure in document/pages level
        # ---------------------------------------------
        # NOTE: blocks structure might be changed in this step, e.g. promote page header/footer,
        # so blocks structure based process, e.g. calculating margin, parse section should be 
        # run after this step.
        Pages._parse_document(raw_pages)

        # ---------------------------------------------
        # 3. parse structure in page level, e.g. page margin, section
        # ---------------------------------------------
        # parse sections
        for page, raw_page in zip(pages, raw_pages):
            # page margin
            margin = raw_page.calculate_margin(**settings)
            raw_page.margin = page.margin = margin

            # page section
            sections = raw_page.parse_section(**settings)
            page.sections.extend(sections)

        print()

    @staticmethod
    def _parse_document(raw_pages: list):
        '''Parse structure in document/pages level, e.g. header, footer'''
        # 页眉区
        header_height = possible_header_height(raw_pages) + 2
        # 收集页眉元素
        all_header_list = []

        for i, page in enumerate(raw_pages):
            page_header_list = []
            for line in page.blocks:
                if line.bbox[3] != 0 and line.bbox[3] < header_height:
                    page_header_list.append(line)
            all_header_list.append(page_header_list)

        print()

        # 每页候选页眉元素数量
        item_count_list = [len(page_header_list) for page_header_list in all_header_list]
        most_common_length = Counter(item_count_list).most_common(1)[0][0]
        # 找到第一个频数最大的
        possible_header_list = next(
            page_header_list for page_header_list in all_header_list if len(page_header_list) == most_common_length)

        # 开始标记页眉元素
        for candidate_line in possible_header_list:
            # 图片
            if "<image>" in candidate_line.text:
                include_cnt = 0
                for page_header_list in all_header_list:
                    for line in page_header_list:
                        if "<image>" in line.text and is_position_matching(line.bbox, candidate_line.bbox):
                            include_cnt += 1
                            break
                if include_cnt / len(raw_pages) > 0.5 and include_cnt > 1:
                    candidate_line.is_header = 1
            # 文字
            elif candidate_line.text:
                include_cnt = 0
                for page_header_list in all_header_list:
                    for line in page_header_list:
                        if remove_number(candidate_line.text) == remove_number(line.text) and is_position_matching(
                                line.bbox, candidate_line.bbox):
                            include_cnt += 1
                            break
                if include_cnt / len(raw_pages) > 0.5 and include_cnt > 1:
                    candidate_line.is_header = 1

        confirmed_header = [candidate_line for candidate_line in possible_header_list if candidate_line.is_header == 1]

        confirmed_header_height = max([header_line.bbox[3] for header_line in confirmed_header])

        # 通过区域去除页眉
        for i, page in enumerate(raw_pages):
            print()
            for line in page.blocks:
                if "<image>" in line.text:
                    if line.bbox[3] != 0 and line.bbox[1] <= confirmed_header_height:
                        line.is_header = 1
                else:
                    if line.bbox[3] != 0 and line.bbox[3] <= confirmed_header_height:
                        line.is_header = 1
        print()


# 页眉区划定
def possible_header_height(raw_pages):
    header_height_list = []
    # 处理页眉
    i = 0
    for raw_page in raw_pages:
        # 页眉高度阈值
        first_line_height = get_first_line_height(raw_page)
        first_text_height = get_first_text_height(raw_page)
        if first_line_height:
            header_height_list.append(first_line_height)
        else:
            header_height_list.append(min(first_text_height, raw_page.height / 10))
        print()
    print()

    text_counter = Counter(header_height_list)
    frequency, most_common_value = text_counter.most_common(1)[0][1], text_counter.most_common(1)[0][0]
    if most_common_value is None:
        return 0
    if frequency / len(header_height_list) > 0.5 and frequency > 1:
        return most_common_value
    return 0


# 获取首次出现文字高度
def get_first_text_height(page):
    for line in page.blocks:
        if line.text and line.bbox[3] != 0:
            return line.bbox[3]
    assert ("")  # todo 删除此行就ok
    return 0


# 获取首次出现大横线高度
def get_first_line_height(page):
    # todo asdf = page.sections[1][0].shapes[0].x0
    for stroke in page.shapes:
        if isinstance(stroke, Stroke) and is_header_horizontal_line(stroke.x0, stroke.y0, stroke.x1, stroke.y1, page.width):
            return stroke.y1
    return 0


# 计算线段是否为页眉横线
def is_header_horizontal_line(x0, y0, x1, y1, width):
    # 宽度大于页面的2/3，且线条粗细小于3
    if (width * 2 / 3) < x1 - x0 and y1 - y0 < 3:
        return True
    else:
        return False


def is_position_matching(rect1, rect2):
    # 创建两个矩形
    rect1_box = box(rect1.x0, rect1.y0, rect1.x1, rect1.y1)
    rect2_box = box(rect2.x0, rect2.y0, rect2.x1, rect2.y1)

    # 计算交集和并集
    intersection = rect1_box.intersection(rect2_box)
    union = rect1_box.union(rect2_box)

    # 计算面积
    inter_area = intersection.area
    union_area = union.area
    print("占比:", inter_area / union_area)

    return inter_area > 0.7 * union_area


def remove_number(text):
    if text is None:
        return None
    # 在页眉，页脚，经常出现次序编号，首先将这些编号去掉,通过剩余文本的相似度，分析是否是页眉页脚
    chinese_number = r'[(一|二|三|四|五|六|七|八|九|十)万]?[(一|二|三|四|五|六|七|八|九)千]?[(一|二|三|四|五|六|七|八|九)百]?[(一|二|三|四|五|六|七|八|九)十]?[(一|二|三|四|五|六|七|八|九)]?'
    # 使用正则表达式，替换符合pattern中的字符为空
    text = re.sub(chinese_number, '', text)
    # 替换所有的数字为空
    text = re.sub(r'\d+', '', text)
    return text.strip()
