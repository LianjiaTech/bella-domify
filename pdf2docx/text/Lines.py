# -*- coding: utf-8 -*-

'''A group of Line objects.
'''
import re
import string

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
        r'^\s*(\d+\.|[\u2488-\u249B])\s*',  # 数字后跟点
        r'^\s*\d+、\s*',  # 数字后跟顿号
        r'^\s*[一二三四五六七八九十百千万]+、\s*',  # 中文数字后跟顿号
        r'^\s*\d+[\)\]】）]\s*',  # 数字后跟右括号
        r'^\s*[\(\[【（]\d+[\)\]】）]\s*',  # 数字左右括号
        r'^\s*[一二三四五六七八九十百千万]+[\)\]】）]\s*',  # 数字后跟右括号
        r'^\s*[\(\[【（][一二三四五六七八九十百千万]+[\)\]】）]\s*',  # 数字左右括号
        r'^\s*[\u2460-\u2473]\s*',  # （①, ②, ③, ..., ⑲）
        r'^\s*[\u2474-\u2487]\s*',  # （⑴, ⑵, ⑶, ..., ⒇）
        r'^\s*[\u24B6-\u24E9]\s*',  # （Ⓐ, Ⓑ, Ⓒ, ..., ⓩ）
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
        r"^\s*第(?:[一二三四五六七八九十百千万]+|\d+)方面\s*"
    ]
    # 无序列表正则表达式
    UNORDERED_LIST_PATTERN = [
        r'^\s*\u2022\s+',  # 圆点符号
        r'^\s*\u25E6\s+',  # 空心圆点符号
        r'^\s*\u2043\s+',  # 短横线
        r'^\s*\u2219\s+',  # 小实心圆
        r'^\s*\u25CF\s+',  # 大实心圆
        r'^\s*\u25A0\s+',  # 实心方块
        r'^\s*\u25B2\s+',  # 实心上三角形
        r'^\s*\u25BC\s+',  # 实心下三角形
        r'^\s*\u25C6\s+',  # 实心菱形
        r'^\s*\u25CB\s+',  # 空心圆圈
        r'^\s*\u25D8\s+',  # 反向空心圆圈
        r'^\s*\u2605\s+',  # 实心星形
        r'^\s*\u2606\s+',  # 空心星形
        r'^\s*\u2660\s+',  # 黑桃符号
        r'^\s*\u2663\s+',  # 梅花符号
        r'^\s*\u2665\s+',  # 红心符号
        r'^\s*\u2666\s+'  # 方块符号
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
        # recognize ordered & unordered list
        for index, rule in enumerate(Lines.ORDERED_LIST_PATTERN):
            match = re.match(rule, line.text)
            if match:
                line.set_order_list(index + 1)
                break
        for index, rule in enumerate(Lines.UNORDERED_LIST_PATTERN):
            match = re.match(rule, line.text)
            if match:
                line.set_unorder_list(index + 1)
                break

    @property
    def image_spans(self):
        '''Get all ImageSpan instances.'''
        spans = []
        for line in self._instances:
            spans.extend(line.image_spans)
        return spans

    def split_vertically_by_text(self, line_break_free_space_ratio: float, new_paragraph_free_space_ratio: float):
        '''Split lines into separate paragraph by checking text. The parent text block consists of 
        lines with similar line spacing, while lines in other paragraph might be counted when the
        paragraph spacing is relatively small. So, it's necessary to split those lines by checking
        the text contents.

        .. note::
            Considered only normal reading direction, from left to right, from top
            to bottom.
        '''
        rows = self.group_by_physical_rows()

        # skip if only one row
        num = len(rows)
        if num == 1: return rows

        # standard row width with first row excluded, considering potential indentation of fist line
        W = max(row[-1].bbox[2] - row[0].bbox[0] for row in rows[1:])
        H = sum(row[0].bbox[3] - row[0].bbox[1] for row in rows) / num

        # check row by row
        res = []
        lines = Lines()
        punc = tuple(constants.SENTENCE_END_PUNC)
        start_of_para = end_of_para = False  # start/end of paragraph
        start_of_sen = end_of_sen = False  # start/end of sentence
        prev_font, prev_font_size, prev_font_bold = None, None, False
        for row in rows:
            # mulite lines in a row should be in line order
            row.sort_in_line_order()
            cur_font, cur_font_size, cur_font_bold = None, None, False
            if row and row[-1].spans:
                last_span = row[-1].spans[-1]
                if isinstance(last_span, TextSpan):
                    cur_font, cur_font_size, cur_font_bold = last_span.font, last_span.size, bool(last_span.flags & 2 ** 4)
            # when font or font size changes, it's a new sentence, and a new paragraph
            if prev_font and prev_font_size and cur_font and cur_font_size:
                if prev_font != cur_font or abs(
                        prev_font_size - cur_font_size) > 0.5 or prev_font_bold != cur_font_bold:
                    start_of_sen = start_of_para = True
            end_of_sen = row[-1].text.strip().endswith(punc)
            w = row[-1].bbox[2] - row[0].bbox[0]

            # start of sentence and free space at the start -> start of paragraph
            if start_of_sen and (W - w) / H >= new_paragraph_free_space_ratio:
                start_of_para = True

            # end of a sentense and free space at the end -> end of paragraph
            elif end_of_sen and w / W <= 1.0 - line_break_free_space_ratio:
                end_of_para = True

            # take action
            if start_of_para:
                res.append(lines)
                lines = Lines()
                lines.extend(row)
            elif end_of_para:
                lines.extend(row)
                res.append(lines)
                lines = Lines()
            else:
                lines.extend(row)

            # for next round
            start_of_sen = end_of_sen
            start_of_para = end_of_para = False
            prev_font, prev_font_size, prev_font_bold = cur_font, cur_font_size, cur_font_bold

        # close the action
        if lines: res.append(lines)

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
