# -*- coding: utf-8 -*-

'''Collection of :py:class:`~pdf2docx.page.Page` instances.'''

import logging
import re
from collections import Counter
import fitz

from shapely.geometry import box

from .RawPageFactory import RawPageFactory
from ..common.Collection import BaseCollection
from ..font.Fonts import Fonts
from ..shape.Shape import Stroke
from ..layout.Blocks import Blocks

PAGE_MARGIN = 90
FREQUENCY_THRESHOLD_TIMES = 2  # 频次阈值
FREQUENCY_THRESHOLD_RATE = 0.4  # 频率阈值 原因：某些文档单双页的页眉不同，所以该值要小于0.5


def get_title_list(fitz_doc):
    title_list = []  # 从目录提取出的title
    toc_data = fitz.utils.get_toc(fitz_doc)
    for item in toc_data:
        level, title, page = item
        title_list.append(title.strip().replace(' ', ''))
    return title_list


class Pages(BaseCollection):
    '''A collection of ``Page``.'''

    def parse(self, fitz_doc, **settings):
        '''Analyze document structure, e.g. page section, header, footer.

        Args:
            fitz_doc (fitz.Document): ``PyMuPDF`` Document instance.
            settings (dict): Parsing parameters.
        '''
        # 返回的元数据
        metadata = {
            "catalog_title_list": get_title_list(fitz_doc)
        }

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
        metadata = Pages._parse_document(raw_pages, pages, metadata, **settings)

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

        return metadata

    @staticmethod
    def _parse_document(raw_pages: list, pages: list, metadata: dict, **settings):
        '''Parse structure in document/pages level, e.g. header, footer'''

        # 页眉页脚解析
        _parser_header_and_footer(raw_pages)

        # 封面解析
        try:
            _parser_cover(raw_pages, pages, settings.get("filter_cover"))
        except Exception as e:
            logging.error(f"Parser cover failed: {e}")

        # 目录解析
        catalog_title_list = parse_catalog(raw_pages, pages, settings.get("filter_catalog", True))
        metadata["catalog_title_list"].extend(catalog_title_list)

        # Title识别(根据文字内容)
        parse_title(raw_pages, pages, metadata)

        return metadata


def parse_title(raw_pages, pages, metadata):
    for i, page in enumerate(raw_pages):
        for line in page.blocks:
            text = line.text.strip().replace(' ', '')
            if text in metadata["catalog_title_list"]:
                line.is_in_catalog = 1
            else:
                line.is_in_catalog = 0


def _parser_cover(raw_pages: list, pages: list, need_filter=False):
    """判断是否为封面
    只解析第一页。判断为封面条件为：首先去掉图片，然后判断空白区域 > 50% 则为封面
    """
    logging.info('parser_cover [start]')

    raw_text = ""
    first_page_size = raw_pages[0].shapes.bbox.width * raw_pages[0].shapes.bbox.height
    if first_page_size == 0:
        first_page_size = max(raw_pages[0].width - PAGE_MARGIN * 2, 0) * max(raw_pages[0].height - PAGE_MARGIN * 2, 0)
        if first_page_size == 0:
            return
    blank_size = first_page_size
    for line in raw_pages[0].blocks:
        # 不算页眉、footer、图片
        if line.is_header or line.is_footer:
            continue
        # 过滤面积占比较大的图片，这部分图片可能是背景图
        if line.image_spans:
            if (img_size := line.bbox.width * line.bbox.height) / first_page_size < 0.6:
                blank_size -= img_size
            continue
        # TODO 暂未考虑 line 重叠的情况
        blank_size -= (line.bbox.width * line.bbox.height)
        raw_text += line.raw_text

    is_cover = (len(raw_pages) >= 3  # 至少有 3 页
                and len(raw_text) <= 200  # 文本长度小于 200
                and (
                        first_page_size == 0.0  # 去除页眉、页脚、图片后，第一页为空
                        or blank_size / first_page_size > 0.5  # 空白区域 > 50%
                )
                )

    if is_cover:
        for line in raw_pages[0].blocks:
            line.tags["Cover"] = 1
        if need_filter:
            raw_pages.pop(0)
            pages.pop(0)

    print("\n【识别封面结果】" + ("存在\n" if is_cover else "不存在\n"))
    logging.info('parser_cover [finish]')


def parse_catalog(raw_pages, pages, need_filter=True):
    """
    目录识别，通过正则表达式匹配目录的特征，目录认定要求：一个短字符串的line + 至少连续3个line能被目录正则式匹配
    """
    logging.info('parse_catalog [start]')
    catalog_title_list = []

    pattern = re.compile(r'(.)\1{9,}\d+')
    found_catalog = False
    catalog_blocks = []
    previous_blocks = None

    search_range = max(3, len(raw_pages) // 3)
    blocks_list = [r for page in raw_pages[:search_range] for r in page.blocks.group_by_physical_rows(sorted=True)]
    for blocks in blocks_list:
        text = "".join([block.text.strip().replace(' ', '') for block in blocks])
        if len(pattern.findall(text)) >= 3:  # 如果在一个block找到多次匹配，那么命中了包含多行目录体的block
            found_catalog = True
            catalog_blocks.append(blocks)
            if is_catalog_title(previous_blocks):
                catalog_blocks.insert(0, previous_blocks)
            continue

        if pattern.search(text):
            catalog_blocks.append(blocks)
            if len(catalog_blocks) == 3:
                # 检查前一个line是否是"目录"两个字
                if is_catalog_title(previous_blocks):
                    catalog_blocks.insert(0, previous_blocks)
        else:
            # 目录已找全
            if len(catalog_blocks) >= 3 or found_catalog:
                break
            # 并非真正目录，重置，继续寻找
            else:
                catalog_blocks = []
                previous_blocks = blocks

    # 目录识别结果打印
    if len(catalog_blocks) >= 3 or found_catalog:
        print("\n【识别目录结果】\n")
        page_lines = {str(r.bbox): r for page in raw_pages[:search_range] for r in page.blocks}
        for c_blocks in catalog_blocks:
            if line := page_lines.get(str(c_blocks[0].bbox)):
                line.is_catalog = 1
            catalog_item = "".join([c_block.text for c_block in c_blocks])
            catalog_title = re.sub(pattern, '', catalog_item.strip().replace(' ', ''))
            catalog_title_list.append(catalog_title)
            print(catalog_item)
    else:
        print("\n【未识别到目录】\n")

    if need_filter:
        catalog_blocks_bbox = [block.bbox for blocks in catalog_blocks for block in blocks]
        for page in raw_pages[:search_range]:
            page.blocks = Blocks(instances=[line for line in page.blocks if line.bbox not in catalog_blocks_bbox],
                                 parent=page)
    logging.info('parser_catalog [finish]')
    return catalog_title_list


def _parser_header_and_footer(raw_pages: list):
    logging.info('parser_header_and_footer [start]')

    identify_header(raw_pages)
    identify_footer(raw_pages)
    for raw_page in raw_pages:
        raw_page.blocks = \
            Blocks(instances=[line for line in raw_page.blocks if (not line.is_header and not line.is_footer)],
                   parent=raw_page)

    logging.info('parser_header_and_footer [finish]')


def identify_header(raw_pages: list):
    """
    识别页眉
    """

    # 页眉区
    header_height = possible_header_height(raw_pages)
    # 收集页眉元素
    all_header_list = []

    for i, page in enumerate(raw_pages):
        page_header_list = []
        for line in page.blocks:
            if line.bbox[3] != 0 and line.bbox[3] < header_height:
                page_header_list.append(line)
        all_header_list.append(page_header_list)

    # 所有疑似页眉元素
    possible_header_list = []
    for page_header_list in all_header_list[:30]:  # 考虑性能，只拿前30页的元素来认定
        possible_header_list.extend(page_header_list)

    # 开始纵向对比，确定页眉元素
    for candidate_line in possible_header_list:
        # 图片
        if "<image>" in candidate_line.text:
            include_cnt = 0
            for page_header_list in all_header_list:
                for line in page_header_list:
                    if "<image>" in line.text and is_position_matching(line.bbox, candidate_line.bbox):
                        include_cnt += 1
                        break
            if include_cnt / len(raw_pages) >= FREQUENCY_THRESHOLD_RATE and include_cnt >= FREQUENCY_THRESHOLD_TIMES:
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
            if include_cnt / len(raw_pages) >= FREQUENCY_THRESHOLD_RATE and include_cnt >= FREQUENCY_THRESHOLD_TIMES:
                candidate_line.is_header = 1

    confirmed_header = [candidate_line for candidate_line in possible_header_list if candidate_line.is_header == 1]
    if not confirmed_header:  # 若没有识别到任何页眉元素
        print("\n【未识别到页眉】\n")
        return

    confirmed_header_height = max([header_line.bbox[3] for header_line in confirmed_header])
    print("\n【页眉区域高度】", confirmed_header_height, "px (", round(raw_pages[0].height, 1), "px )\n")

    # 通过区域去除页眉
    for i, page in enumerate(raw_pages):
        for line in page.blocks:
            if "<image>" in line.text:
                if line.bbox[3] != 0 and line.bbox[1] <= confirmed_header_height:
                    line.is_header = 1
            else:
                if line.bbox[3] != 0 and line.bbox[3] <= confirmed_header_height:
                    line.is_header = 1


def identify_footer(raw_pages: list):
    """
    识别页脚
    """

    # 页脚区: 页脚一般没有大横线、故召回时应该放大一些范围，这里取 20%
    footer_height = (raw_pages[0].height * 8 / 10) - 10
    # 收集页脚元素
    all_footer_list = []

    for i, page in enumerate(raw_pages):
        page_footer_list = []
        for line in page.blocks:
            if line.bbox[1] != 0 and footer_height < line.bbox[1]:
                page_footer_list.append(line)
        all_footer_list.append(page_footer_list)

    # 所有疑似页脚元素
    possible_footer_list = []
    for page_footer_list in all_footer_list[:30]:  # 考虑性能，只拿前30页的元素来认定
        possible_footer_list.extend(page_footer_list)

    # 开始纵向对比，确定页脚元素
    for candidate_line in possible_footer_list:
        # 图片
        if "<image>" in candidate_line.text:
            include_cnt = 0
            for page_footer_list in all_footer_list:
                for line in page_footer_list:
                    if "<image>" in line.text and is_position_matching(line.bbox, candidate_line.bbox):
                        include_cnt += 1
                        break
            if include_cnt / len(raw_pages) >= FREQUENCY_THRESHOLD_RATE and include_cnt >= FREQUENCY_THRESHOLD_TIMES:
                candidate_line.is_footer = 1
        # 文字
        elif candidate_line.text:
            include_cnt = 0
            for page_footer_list in all_footer_list:
                for line in page_footer_list:
                    if remove_number(candidate_line.text) == remove_number(line.text) and is_position_matching(
                            line.bbox, candidate_line.bbox):
                        include_cnt += 1
                        break
            if include_cnt / len(raw_pages) >= FREQUENCY_THRESHOLD_RATE and include_cnt >= FREQUENCY_THRESHOLD_TIMES:
                candidate_line.is_footer = 1

    confirmed_footer = [candidate_line for candidate_line in possible_footer_list if candidate_line.is_footer == 1]
    if not confirmed_footer:  # 若没有识别到任何页脚元素
        print("\n【未识别到页脚】\n")
        return

    confirmed_footer_height = min([footer_line.bbox[1] for footer_line in confirmed_footer])

    print("\n【页脚区域高度】", confirmed_footer_height, "px (", round(raw_pages[0].height, 1), "px )\n")

    # 通过区域去除页脚
    for i, page in enumerate(raw_pages):
        for line in page.blocks:
            # 页脚部分图片和文字处理相同，必须整个bbox处于页脚区
            if confirmed_footer_height <= line.bbox[1]:
                line.is_footer = 1


# 页眉区划定
def possible_header_height(raw_pages):
    header_height_list = []
    # 处理页眉
    for raw_page in raw_pages:
        # 页眉高度阈值
        first_line_height = get_first_line_height(raw_page) + 5
        if first_line_height:
            header_height_list.append(first_line_height)
        else:
            header_height_list.append(raw_page.height / 10)

    text_counter = Counter(header_height_list)
    frequency, most_common_value = text_counter.most_common(1)[0][1], text_counter.most_common(1)[0][0]
    if most_common_value is None:
        return 0
    if frequency / len(header_height_list) >= FREQUENCY_THRESHOLD_RATE and frequency >= FREQUENCY_THRESHOLD_TIMES:
        return most_common_value
    return 0


# 获取首次出现大横线高度
def get_first_line_height(page):
    for stroke in page.shapes:
        if (isinstance(stroke, Stroke)
                and is_horizontal_line(stroke.x0, stroke.y0, stroke.x1, stroke.y1, page.width)
                and stroke.y1 < (page.height / 4)):
            height = stroke.y1
            return height
    else:
        return 0


# 计算线段是否为页眉横线
def is_horizontal_line(x0, y0, x1, y1, width):
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


def is_catalog_title(blocks):
    """
    目录标题判断
    """
    return blocks and "".join([b.text for b in blocks]).strip().replace(" ", "") in ["目录", "目次"]
