# -*- coding: utf-8 -*-

'''A group of Line objects.
'''
import re
import string
from collections import Counter

from .Line import Line
from .TextSpan import TextSpan
from ..common import constants
from ..common.Collection import ElementCollection
from ..common.share import TextAlignment
from ..image.ImageSpan import ImageSpan


class Lines(ElementCollection):
    '''Collection of text lines.'''

    # 有序列表正则表达式
    ORDERED_LIST_PATTERN = [
        r'^\s*\d+\.\d+\.\d+\.\d+\.\d+\.\d+\.\d+',  # 数字后跟点 1.2.3.4.5.6.7
        r'^\s*\d+\.\d+\.\d+\.\d+\.\d+\.\d+',  # 数字后跟点
        r'^\s*\d+\.\d+\.\d+\.\d+\.\d+',  # 数字后跟点
        r'^\s*\d+\.\d+\.\d+\.\d+',  # 数字后跟点
        r'^\s*\d+\.\d+\.\d+',  # 数字后跟点 1.23.45
        r'^\s*\d+\.\d+',  # 数字后跟点 匹配案例：1.23 和 1.23.
        r'^\s*\d+\.[^\d]',  # 数字后跟点 1.
        # r'^\s*\d+\.\s*',  # 数字后跟点
        r'^\s*[\u2488-\u249B]\s*',  # 数字后跟点
        r'^\s*\d+、\s*',  # 数字后跟顿号
        r'^\s*[一二三四五六七八九十百千万]+、\s*',  # 中文数字后跟顿号
        r'^\s*\d+[\)\]】）]\s*',  # 数字后跟右括号
        r'^\s*[\(\[【（]\d+[\)\]】）]\s*',  # 数字左右括号
        r'^\s*[一二三四五六七八九十百千万]+[\)\]】）]\s*',  # 数字后跟右括号
        r'^\s*[\(\[【（][一二三四五六七八九十百千万]+[\)\]】）]\s*',  # 数字左右括号
        r'^\s*[a-z][\)\]】）]\s*',  # 小写英文字母后跟右括号
        r'^\s*[A-Z][\)\]】）]\s*',  # 大写英文字母后跟右括号
        r'^\s*[\u2460-\u2473]\s*',  # （①, ②, ③, ..., ⑲）
        r'^\s*[\u2474-\u2487]\s*',  # （⑴, ⑵, ⑶, ..., ⒇）
        r'^\s*[\u24B6-\u24E9]\s*',  # （Ⓐ, Ⓑ, Ⓒ, ..., ⓩ）
        r'^\s*\[\d+\]\s*',          # （[1],[2],[3] ... [11]）
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)篇\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)章\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)节\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)条\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)项\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)步\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)点\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)部分\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)部\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)段\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)例\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)个\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)阶段\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)层面\s*",
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)方面\s*",
        r".*\s*(.)\1{9,}\s*\d+\s*$"                            # 目录项
    ]
    # 记得同步修改ORDERED_LIST_FIRST_ITEM_PATTERN！！！

    ORDERED_LIST_FIRST_ITEM_PATTERN = [
        r'^\s*1\.\s*',  # 数字1后跟点
        r'^\s*[\u2488]\s*',  # 数字1后跟点
        r'^\s*1、\s*',  # 数字1后跟顿号
        r'^\s*一、\s*',  # 中文数字一后跟顿号
        r'^\s*1[\)\]】）]\s*',  # 数字1后跟右括号
        r'^\s*[\(\[【（]1[\)\]】）]\s*',  # 数字1左右括号
        r'^\s*一[\)\]】）]\s*',  # 中文数字一后跟右括号
        r'^\s*[\(\[【（]一[\)\]】）]\s*',  # 中文数字一左右括号
        r'^\s*a[\)\]】）]\s*',  # 小写英文字母a后跟右括号
        r'^\s*A[\)\]】）]\s*',  # 大写英文字母A后跟右括号
        r'^\s*[\u2460]\s*',  # （①）
        r'^\s*[\u2474]\s*',  # （⑴）
        r'^\s*[\u24B6]\s*',  # （Ⓐ）
        r'^\s*\[1\]\s*',  # （[1]）
        r"^\s*第(?:一|1)篇\s*",
        r"^\s*第(?:一|1)章\s*",
        r"^\s*第(?:一|1)节\s*",
        r"^\s*第(?:一|1)条\s*",
        r"^\s*第(?:一|1)项\s*",
        r"^\s*第(?:一|1)步\s*",
        r"^\s*第(?:一|1)点\s*",
        r"^\s*第(?:一|1)部分\s*",
        r"^\s*第(?:一|1)部\s*",
        r"^\s*第(?:一|1)段\s*",
        r"^\s*第(?:一|1)例\s*",
        r"^\s*第(?:一|1)个\s*",
        r"^\s*第(?:一|1)阶段\s*",
        r"^\s*第(?:一|1)层面\s*",
        r"^\s*第(?:一|1)方面\s*",
        r".*\s*(.)\1{9,}\s*1\s*$"  # 目录项
    ]

    @property
    def unique_parent(self):
        '''Whether all contained lines have same parent.'''
        if not bool(self): return False

        first_line = self._instances[0]
        return all(line.same_source_parent(first_line) for line in self._instances)

    def restore(self, raws: list):
        '''Construct lines from raw dicts list.'''
        for raw in raws:
            line = Line(raw)
            self.recognize_list(line)
            self.append(line)
        return self

    def recognize_list(self, line: Line):

        # def recognize_list_first_item(text, index):
        #     if re.match(Lines.ORDERED_LIST_PATTERN[index], text.replace(" ", "")):
        #         return True
        #     else:
        #         return False

        # recognize ordered & unordered list
        for index, rule in enumerate(Lines.ORDERED_LIST_PATTERN):
            if match := re.match(rule, line.text.replace(" ", "")):
                line.list_type = index + 1
                line.list_tag = match.group(0)
                # line.list_first_item = recognize_list_first_item(line.text, index)
                return

        def is_special_start_character(s):
            if not s:
                return False, None
            # 定义一个正则表达式模式，匹配非字母数字、空格、中文字符和常用标点符号
            pattern = re.compile(r'^[^\w\s\u4e00-\u9fff.,!?;:\[\](){}\\/\'"“”‘’]')
            if match := pattern.match(s):
                return True, match.group(0)
            return False, None

        result, char = is_special_start_character(line.text)
        if result:
            line.list_type = char
            line.list_tag = char
            return

    @property
    def image_spans(self):
        '''Get all ImageSpan instances.'''
        spans = []
        for line in self._instances:
            spans.extend(line.image_spans)
        return spans

    # 获取lines的字体字号与加粗
    def get_font_size_bold(self):

        # 字体
        font_list = [span.font for line in self._instances for span in line.spans]
        font_counter = Counter(font_list)
        font_most_common_value = font_counter.most_common(1)[0][0]

        # 字号
        size_list = [span.size for line in self._instances for span in line.spans]
        size_counter = Counter(size_list)
        size_most_common_value = size_counter.most_common(1)[0][0]

        # 加粗
        # flags代表用于表示文本的格式化属性，每一位代表不同的格式化属性(粗体、斜体、下划线)
        # 全为True时，才返回加粗（一半文字加粗一半不加粗，应视为不加粗的文字块）
        if all([bool(span.flags & 2 ** 4) for line in self._instances for span in line.spans]) or all(
                [span.pseudo_bold for line in self._instances for span in line.spans]):
            bold_most_common_value = True
        else:
            bold_most_common_value = False

        return font_most_common_value, size_most_common_value, bold_most_common_value

    def split_vertically_by_text(self, text_left_x: float, text_right_x: float):
        '''Split lines into separate paragraph by checking text. The parent text block consists of 
        lines with similar line spacing, while lines in other paragraph might be counted when the
        paragraph spacing is relatively small. So, it's necessary to split those lines by checking
        the text contents.

        .. note::
            Considered only normal reading direction, from left to right, from top
            to bottom.
        
        .. return::
            [[block, is_start_of_para, is_end_of_para], ...]
        '''
        rows = self.group_by_physical_rows()
        # skip if only one row
        if len(rows) == 1:
            if rows[0][0].is_list:
                return [[rows[0], True, True]]
            else:
                return [[rows[0], True, False]]

        # check row by row
        res = []
        lines = Lines()
        start_of_para, end_of_para = False, False  # start/end of paragraph
        prev_row = None

        for row in rows:
            # multi lines in a row should be in line order
            row.sort_in_line_order()
            word_w = (row[0].bbox[2] - row[0].bbox[0]) / len(row[0].text)
            
            # 1. 列表项缩进特殊处理，例如
            #   【1】 xxxxxx
            #        xxxxxx
            if row and not row[0].is_list and lines and lines[0].is_list and \
                    text_right_x - lines[0].bbox[2] < 1.5 * word_w and \
                    row[0].bbox[0] - lines[0].bbox[0] < (word_w * (len(lines[0].list_tag) + 1.5)):
                start_of_para = False
            # 2 首行缩进则判断为段首
            elif row and row[0] and row[0].bbox[0] - text_left_x > (word_w * 1.5):
                start_of_para = True
            elif prev_row:
                # 获取上一行的字体、字号、粗体信息
                prev_font, prev_font_size, prev_font_bold = None, None, False
                if prev_row[-1].spans and isinstance((prev_last_span := prev_row[-1].spans[-1]), TextSpan):
                    prev_font, prev_font_size, prev_font_bold = prev_row.get_font_size_bold()
                # 获取当前行的字体、字号、粗体信息
                cur_font, cur_font_size, cur_font_bold = None, None, False
                if row and row[-1].spans and isinstance((first_span := row[-1].spans[0]), TextSpan):
                    cur_font, cur_font_size, cur_font_bold = row.get_font_size_bold()
                # 3 当前行的字体和字号与上一行不同时，判断为段首
                # when font or font size changes, it's a new sentence, and a new paragraph
                if prev_font_size and cur_font_size:
                    if abs(prev_font_size - cur_font_size) > 0.5 or prev_font_bold != cur_font_bold:
                        start_of_para = True

            if text_right_x - row[-1].bbox[2] > 2 * word_w:
                end_of_para = True

            # 如果是段落首句，将之前缓存的lines放入结果res，然后将当前row放入缓存lines
            if start_of_para:
                if lines:
                    # 识别出是新一段的开始，说明之前缓存的段落已经结束
                    res.append((lines, start_of_para, True))
                lines = Lines()
            lines.extend(row)
            # 如果是段落尾句，将之前缓存的lines放入结果res，清空缓存lines
            if end_of_para:
                res.append((lines, start_of_para, end_of_para))
                lines = Lines()
            # for next round
            start_of_para = end_of_para = False
            prev_row = row

        # close the action
        if lines:
            res.append((lines, start_of_para, end_of_para))
        return res

    def adjust_last_word(self, delete_end_line_hyphen: bool):
        '''Adjust word at the end of line:
        # - it might miss blank between words from adjacent lines
        # - it's optional to delete hyphen since it might not at the the end 
           of line after conversion
        '''
        punc_ex_hyphen = ''.join(c for c in string.punctuation if c != '-')

        def is_end_of_english_word(c):
            return c.isalnum() or (c and c in punc_ex_hyphen)

        for i, line in enumerate(self._instances[:-1]):
            # last char in this line
            end_span = line.spans[-1]
            if not isinstance(end_span, TextSpan): continue
            end_chars = end_span.chars
            if not end_chars: continue
            end_char = end_chars[-1]

            # first char in next line
            start_span = self._instances[i + 1].spans[0]
            if not isinstance(start_span, TextSpan): continue
            start_chars = start_span.chars
            if not start_chars: continue
            next_start_char = start_chars[0]

            # delete hyphen if next line starts with lower case letter
            if delete_end_line_hyphen and \
                    end_char.c.endswith('-') and next_start_char.c.islower():
                end_char.c = ''  # delete hyphen in a tricky way

            # add a space if both the last char and the first char in next line are alphabet,
            # number, or English punctuation (excepting hyphen)
            if is_end_of_english_word(end_char.c) and is_end_of_english_word(next_start_char.c):
                end_char.c += ' '  # add blank in a tricky way

    def parse_text_format(self, shape):
        '''Parse text format with style represented by rectangle shape.
        
        Args:
            shape (Shape): Potential style shape applied on blocks.
        
        Returns:
            bool: Whether a valid text style.
        '''
        flag = False

        for line in self._instances:
            # any intersection in this line?
            expanded_bbox = line.get_expand_bbox(constants.MAJOR_DIST)
            if not shape.bbox.intersects(expanded_bbox):
                if shape.bbox.y1 < line.bbox.y0: break  # lines must be sorted in advance
                continue

            # yes, then try to split the spans in this line
            split_spans = []
            for span in line.spans:
                # include image span directly
                if isinstance(span, ImageSpan):
                    split_spans.append(span)

                # split text span with the format rectangle: span-intersection-span
                else:
                    spans = span.split(shape, line.is_horizontal_text)
                    split_spans.extend(spans)
                    flag = True

            # update line spans                
            line.spans.reset(split_spans)

        return flag

    def parse_line_break(self, bbox,
                         line_break_width_ratio: float,
                         line_break_free_space_ratio: float):
        '''Whether hard break each line. 

        Args:
            bbox (Rect): bbox of parent layout, e.g. page or cell.
            line_break_width_ratio (float): user defined threshold, break line if smaller than this value.
            line_break_free_space_ratio (float): user defined threshold, break line if exceeds this value.

        Hard line break helps ensure paragraph structure, but pdf-based layout calculation may
        change in docx due to different rendering mechanism like font, spacing. For instance, when
        one paragraph row can't accommodate a Line, the hard break leads to an unnecessary empty row.
        Since we can't 100% ensure a same structure, it's better to focus on the content - add line
        break only when it's necessary to, e.g. short lines.
        '''

        block = self.parent
        idx0, idx1 = (0, 2) if block.is_horizontal_text else (3, 1)
        block_width = abs(block.bbox[idx1] - block.bbox[idx0])
        layout_width = bbox[idx1] - bbox[idx0]

        # hard break if exceed the width ratio
        line_break = block_width / layout_width <= line_break_width_ratio

        # check by each physical row
        rows = self.group_by_physical_rows()
        for lines in rows:
            for line in lines: line.line_break = 0

            # check the end line depending on text alignment
            if block.alignment == TextAlignment.RIGHT:
                end_line = lines[0]
                free_space = abs(block.bbox[idx0] - end_line.bbox[idx0])
            else:
                end_line = lines[-1]
                free_space = abs(block.bbox[idx1] - end_line.bbox[idx1])

            if block.alignment == TextAlignment.CENTER: free_space *= 2  # two side space

            # break line if 
            # - width ratio lower than the threshold; or 
            # - free space exceeds the threshold
            if line_break or free_space / block_width > line_break_free_space_ratio:
                end_line.line_break = 1

        # no break for last row
        for line in rows[-1]: line.line_break = 0

    def parse_tab_stop(self, line_separate_threshold: float):
        '''Calculate tab stops for parent block and whether add TAB stop before each line. 

        Args:
            line_separate_threshold (float): Don't need a tab stop if the line gap less than this value.
        '''
        # set all tab stop positions for parent block
        # Note these values are relative to the left boundary of parent block
        block = self.parent
        idx0, idx1 = (0, 2) if block.is_horizontal_text else (3, 1)
        fun = lambda line: round(abs(line.bbox[idx0] - block.bbox[idx0]), 1)
        all_pos = set(map(fun, self._instances))
        tab_stops = list(filter(lambda pos: pos >= constants.MINOR_DIST, all_pos))
        tab_stops.sort()  # sort in order
        block.tab_stops = tab_stops

        # no tab stop need
        if not block.tab_stops: return

        def tab_position(pos):  # tab stop index of given position
            # 0   T0  <pos>  T1    T2
            i = 0
            pos -= block.bbox[idx0]
            for t in tab_stops:
                if pos < t: break
                i += 1
            return i

        # otherwise, set tab stop option for each line
        # Note: it might need more than one tab stops
        # https://github.com/dothinking/pdf2docx/issues/157
        ref = block.bbox[idx0]
        for i, line in enumerate(self._instances):
            # left indentation implemented with tab
            distance = line.bbox[idx0] - ref
            if distance > line_separate_threshold:
                line.tab_stop = tab_position(line.bbox[idx0]) - tab_position(ref)

            # update stop reference position
            if line == self._instances[-1]: break
            ref = line.bbox[idx1] if line.in_same_row(self._instances[i + 1]) else block.bbox[idx0]
