# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/9/11
#    @Description   : 
#
# ===============================================================
import copy
import datetime
import json
import logging
import os
import re
from collections import defaultdict
from difflib import SequenceMatcher
from statistics import mean

import fitz
import markdown
import pandas as pd
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from shapely.geometry import box

import parse_output as beike_parse_output
from constant import file_list, parser_list


def log_setting(log_file=""):
    if not log_file:
        raise "log_file is none"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 创建一个日志记录器
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.INFO)  # 设置日志级别
    formatter = logging.Formatter('%(message)s')

    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = log_setting(log_file='reports/all/output_indicators_' + datetime.datetime.now().strftime('%Y%m%d_%H点%M分') + '.txt')

print_setting = {
    "PRINT_1V1_TEXT": 1,  # 打印1v1映射的text
    "PRINT_MAP": 1,  # 打印映射关系
    "PRINT_MAP_": 1,  # 打印映射关系
}


block_type_mapping = {
    "Catalog": "text",
    "Title": "text",
    "List": "text",
    "Formula": "text",
    "Code": "text",
    "Text": "text",

    "Figure": "image",
    "FigureName": "text",
    "FigureNote": "text",

    "Table": "table",
    "TableName": "text",
    "TableNote": "text",
}

block_type = [
    "Text",
    "Title",
    "List",
    "Catalog",
    "Table",
    "Figure",
    "Formula",
    "Code",
    "FigureName",
    "FigureNote",
    "TableName",
    "TableNote",
]

parse_str = "p_"


def load_json(file_path):
    with open(file_path, 'r') as file:
        # 读取 JSON 数据
        data = json.load(file)
    return data


def load_markdown(file_path):
    # 读取Markdown文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        markdown_content = file.read()

    # 初始化Markdown解析器
    md = MarkdownIt()
    # 解析Markdown内容为tokens
    tokens = md.parse(markdown_content)

    tag2type = {
        "h1": "Title",
        "h2": "Title",
        "h3": "Title",
        "h4": "Title",
        "p": "Text",
        "ol": "List",  # 有序列表
        "li": "List",
        "ul": "List",  # 无序列表
        "code": "Code",  # 无序列表
        "": "",
    }

    def compress_items(type_list):
        if "List" in type_list:
            return "List"
        elif "Title" in type_list:
            return "Title"
        else:
            return "Text"

    def cut_string(s):
        first_index = s.find("|")
        last_index = s.rfind("|")

        if first_index == -1 or last_index == -1 or first_index == last_index:
            return "", s

        # 切出字符
        cut_part = s[first_index:last_index + 1]
        # 剩余的字符串
        remaining_part = s[:first_index] + s[last_index + 1:]

        return cut_part, remaining_part

    def html_to_table(html_content):
        table_md_text = ""
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table')

        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            col_texts = [col.get_text(strip=True) for col in cols]
            table_md_text += '|'.join(col_texts)+"|"

        return '|' + table_md_text

    type_list = []
    contents = []
    index = 0
    for token in tokens:
        item_type = tag2type[token.tag]
        item_text = token.content.strip().replace(" ", "")

        if token.type.endswith('_open'):
            type_list.append(item_type)
        elif token.type.endswith('_close'):
            type_list = []
        # 内容
        else:
            # 尝试抽取表格
            table_text, item_text = cut_string(item_text)
            if table_text:
                current_element_new = {
                    'page_num': -1,
                    'order_num': str(index),
                    'type': "Table",
                    'layout_type': "Table",
                    'text': table_text.replace("---|", ""),
                }
                index += 1
                contents.append(current_element_new)

            # Figure
            if token.type == "html_block" and "<!-- image -->" in item_text:
                current_element_new = {
                    'page_num': -1,
                    'order_num': str(index),
                    'type': "Figure",
                    'layout_type': "Figure",
                    'text': "<image>",
                }
                index += 1
                contents.append(current_element_new)
            elif "![](images/" in item_text:
                current_element_new = {
                    'page_num': -1,
                    'order_num': str(index),
                    'type': "Figure",
                    'layout_type': "Figure",
                    'text': "<image>",
                }
                index += 1
                contents.append(current_element_new)

            # Table
            elif token.type == "html_block" and "<table>" in item_text:
                table_text = html_to_table(item_text)
                current_element_new = {
                    'page_num': -1,
                    'order_num': str(index),
                    'type': "Table",
                    'layout_type': "Table",
                    'text': table_text,
                }
                index += 1
                contents.append(current_element_new)

            # Code
            elif token.type == "fence" and token.tag == "code":
                current_element_new = {
                    'page_num': -1,
                    'order_num': str(index),
                    'type': "Code",
                    'layout_type': "Code",
                    'text': item_text,
                }
                index += 1
                contents.append(current_element_new)
            # Text
            elif item_text:
                final_type = compress_items(type_list)
                for slice in item_text.split('\n'):
                    current_element_new = {
                        'page_num': -1,
                        'order_num': str(index),
                        'type': final_type,
                        'layout_type': final_type,
                        'text': slice,
                    }
                    index += 1
                    contents.append(current_element_new)

    return contents


def load_markdown2(file_path):

    def extract_table(text):
        # 使用正则表达式匹配从第一个到最后一个竖线之间的内容
        match = re.search(r'\|.*\|', text, re.DOTALL)
        if match:
            return match.group(0)
        return None

    # 读取Markdown文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        markdown_content = file.read()

    # 将Markdown转换为HTML
    html = markdown.markdown(markdown_content)

    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html, 'html.parser')

    # 提取元素及其内容
    nodes = []
    for index, element in enumerate(soup.find_all()):
        tag_name = element.name
        content = element.get_text(strip=True)

        table_content = None
        if extract_table(content):
            pass

        if "|\n" in content:
            chunk_type = "Table"
        elif tag_name == "h1":
            chunk_type = "Title"
        elif tag_name == "p":
            chunk_type = "Text"
        else:
            chunk_type = ""
            print()

        node_info = {
            "page_num": -1,  # 从0开始
            "order_num": str(index),
            "type": chunk_type,
            "layout_type": chunk_type,
            "text": content.strip().replace("---|", "").replace(" ", ""),
        }
        nodes.append(node_info)

    return nodes


def edit_distance(s1, s2):
    """计算两个字符串的编辑距离"""
    # 这个函数有个bug，计算编辑距离时不是对称的，暂时先把短的放前边，会好一点
    if len(s1) > len(s2):
        return SequenceMatcher(None, s2, s1).ratio()
    else:
        return SequenceMatcher(None, s1, s2).ratio()


def tree2list_beike(tree):
    """遍历树并返回所有节点的路径和文本"""

    nodes = []
    node = tree

    if tree.get("element"):
        node_type = tree.get("element", {}).get("block_type")
        layout_type = tree.get("element", {}).get("layout_type")
        bbox = tree.get("element", {}).get("bbox")

        page_num = node.get("element", {})["page_num"][0]
        if node_type == "text":
            text = node.get("element", {}).get("text", "")
        elif node_type == "table":
            rows = node.get("element", {}).get("rows", [])
            text = " | ".join(cell["text"] for row in rows for cell in row.get("cells"))
        else:
            text = "<image>"

        order_num = node.get("order_num")

        node_info = {
            "block_type": node_type,
            "layout_type": layout_type,
            "order_num": order_num,
            "text": text,
            "page_num": page_num,
            "bbox": bbox,
        }
        nodes.append(node_info)
    for child in tree.get("children", []):
        nodes.extend(tree2list_beike(child))
    return nodes


def tree2list_adobe(parser_json):
    """遍历树并返回所有节点的路径和文本"""
    nodes = []
    adobe_layout_map = {
        "Aside": "",  # 文档中不属于常规内容流的内容
        "Figure": "",  # 不可重排的构造，如图表、图像、流程图
        "Footnote": "",  # 脚注
        "H": "Title",  # 标题级别
        "H1": "Title",  # 标题级别
        "H2,": "Title",  # 标题级别
        "L": "List",  # 列表
        "Li": "List",  # 列表项
        "Lbl": "",  # 列表项标签
        "Lbody": "",  # 列表项主体
        "P": "Text",  # 段落
        "ParagraphSpan": "",  # 表示段落的一部分。
        "Reference": "",  # 链接
        "Sect": "",  # 文档的逻辑部分
        "StyleSpan": "",  # 表示相对于父容器的文本样式差异
        "Sub ": "",  # 多行段落中的单行（例如地址）。
        "Table": "",  # 表格
        "TD": "",  # 表格单元格
        "TH": "",  # 表格标题单元格
        "TR": "",  # 表格行
        "Title": "",  # 文档的标题。
        "TOC": "",  # 目录
        "TOCI": "",  # 目录项
        "Watermark": "",  # 水印
    }

    elements = parser_json.get("elements", [])
    find_table = False
    table_list = []
    for element in elements:
        text = element.get("Text", "")
        block_type = element["Path"].split('/')[-1]
        layout_type = adobe_layout_map.get(block_type, "")

        if "Table" in element["Path"] and not find_table:
            find_table = True
            if block_type == "P":
                table_list.append(element["Text"])
                continue
            else:
                continue
        elif find_table:
            find_table = False
            text = " | ".join(table_list)
        else:
            if block_type == "Figure":
                text = "<image>"
            else:
                text = element["Text"]
                # pass

        node_info = {
            "block_type": block_type,
            "layout_type": layout_type,
            "order_num": element["Path"],
            "text": text.strip(),
        }
        nodes.append(node_info)

    return nodes


def tree2list_ali(parser_json):
    """遍历树并返回所有节点的路径和文本"""
    nodes = []
    ali_layout_map = {
        "doc_name": "Title",  # 文档名称
        "doc_title": "Title",  # 文档标题
        "doc_subtitle": "Title",  # 文档副标题
        "para_title": "Title",  # 段落标题
        "table_name": "TableName",  # 表格标题
        "table_note": "TableNote",  # 表注
        "formula": "Formula",  # 公式
        "cate_title": "Catalog",  # 目录标题
        "cate": "Catalog",  # 目录主体
        "para": "Text",  # 段落
        "picture": "Figure",  # 图片
        "logo": "Figure",  # logo
        "pic_title": "FigureName",  # 图片标题
        "pic_caption": "FigureNote",  # 图注
        "page_footer": "Text",  # 页脚
        "page_header": "Text",  # 页眉
        "footer_note": "Text",  # 脚注
    }

    elements = parser_json["layouts"]
    for element in elements:
        type = element["type"]
        subType = element["subType"]
        text = element["text"].replace(" ", "")
        page_num = element["pageNum"][0]

        if not text and not (type == "figure" or subType == "picture"):
            continue
        if type in ["head", "head_image", "head_pagenum", "header_line",
                    "foot", "foot_image", "foot_pagenum", ]:
            continue

        if subType == "none":
            if type == "table":
                text = text.replace("|\n", "").replace("---|", "").replace(" ", "")[1:]
                layout_type = "Table"
            elif type == "text":
                layout_type = "Text"
            elif type == "title":
                layout_type = "Title"
            elif type == "table_name":
                layout_type = "TableName"
            elif type == "figure":
                layout_type = "Figure"
                text = "<image>"
            else:
                raise

        else:
            layout_type = ali_layout_map[subType]
            if (type == "figure" or subType == "picture"):
                text = "<image>"

        node_info = {
            "type": type,
            "subType": subType,
            "layout_type": layout_type,
            "order_num": element["uniqueId"],
            "text": text.strip(),
            "page_num": page_num,
            "bbox": element["pos"],
        }
        nodes.append(node_info)

    return nodes


def tree2list_unstructured(parser_json):
    nodes = []
    """
    Element type	Description
    
    Formula	            An element containing formulas in a document.
    FigureCaption	    An element for capturing text associated with figure captions.
    NarrativeText	    NarrativeText is an element consisting of multiple, well-formulated sentences. This excludes elements such titles, headers, footers, and captions.
    ListItem	        ListItem is a NarrativeText element that is part of a list.
    Title	            A text element for capturing titles.
    Address	            A text element for capturing physical addresses.
    EmailAddress	    A text element for capturing email addresses.
    Image	            A text element for capturing image metadata.
    PageBreak	        An element for capturing page breaks.
    Table	            An element for capturing tables.
    Header	            An element for capturing document headers.
    Footer	            An element for capturing document footers.
    CodeSnippet	        An element for capturing code snippets.
    PageNumber	        An element for capturing page numbers.
    UncategorizedText	Base element for capturing free text from within document.
    """

    layout_map = {
        "Formula": "Formula",  # 公式
        "FigureCaption": "FigureName",  # 图题
        "NarrativeText": "Text",  # 段落
        "ListItem": "List",  # 段落 todo 暂时不输出list
        "Title": "Title",
        "Address": "Text",
        "EmailAddress": "Text",
        "Image": "Figure",  # 图片
        "PageBreak": "",  # 暂时未发现这个枚举值
        "Table": "Table",
        "Header": "",  # 页眉
        "Footer": "",  # 页脚
        "CodeSnippet": "Code",
        "PageNumber": "",  # 页码
        "UncategorizedText": "Text",

    }

    elements = parser_json
    for element in elements:
        type = element["type"]
        text = element["text"].replace(" ", "")
        page_num = element["metadata"]["page_number"]

        if type in ["PageBreak", "Header", "Footer", "PageNumber"]:
            continue

        # text修正
        layout_type = layout_map[type]
        if type == "Image":
            text = "<image>"


        node_info = {
            "type": type,
            "layout_type": layout_type,
            "order_num": element["element_id"],
            "text": text.strip(),
            "page_num": page_num -1,
            # "element": tree.get("element", {})
        }
        nodes.append(node_info)

    return nodes


def tree2list_paoding(parser_json):
    nodes = []
    """
    paragraphs	string	段落元素块
    tables	string	表格元素块
    images	string	图片元素块
    page_header	string	页眉元素块
    page_footer	string	页脚元素块
    footnotes
    """

    layout_map = {
        "paragraphs": "Text",  #
        "tables": "Table",  #
        "images": "Figure",  #
        "page_headers": "Text",  #
        "page_footers": "Text",  #
        "footnotes": "FigureNote",  #
        "shapes": "Figure",  # 线框图
    }

    pdf_elements = parser_json["pdf_elements"]
    elements = []
    for page_item in pdf_elements:
        page_num = page_item["page"]
        for element in page_item["elements"]:
            element["page_num"] = page_num
            elements.append(element)

    for element in elements:
        ori_type = element["element_type"]
        text = element.get("text", "").replace(" ", "")

        if ori_type in ["page_headers", "page_footers"]:
            continue

        # text修正
        layout_type = layout_map[ori_type]
        if ori_type == "images":
            text = "<image>"
        elif ori_type == "tables":
            mylist = []
            for k, v in element["cells"].items():
                mylist.append(v["value"])
            text = "|".join(mylist).replace(" ", "")
        if ori_type not in layout_map:
            raise

        node_info = {
            "ori_type": ori_type,
            "layout_type": layout_type,
            "order_num": str(element["origin_index"]),
            "text": text.strip(),
            "page_num": element["page_num"],
            # "element": tree.get("element", {})
        }
        nodes.append(node_info)

    return nodes


def tree2list_chunkr(parser_json):
    nodes = []
    """
  | "Title"
  | "Section header"
  | "Text"
  | "List item"
  | "Table"
  | "Picture"
  | "Caption"
  | "Formula"
  | "Footnote"
  | "Page header"
  | "Page footer"
    """

    layout_map = {
        "Title": "Title",  #
        "Section header": "Title",  #
        "Text": "Text",  #
        "List item": "List",  #
        "Table": "Table",  #
        "Picture": "Figure",  #
        "Caption": "FigureNote",  # 图注表注？？
        "Formula": "Formula",  # 公式
        "Footnote": "",  # 脚注、注释（没有任何元素被识别为这个）
        "Page header": "",  # 页眉
        "Page footer": "",  # 页脚
    }

    elements = []
    for item in parser_json:
        elements.extend(item["segments"])

    print()

    for element in elements:
        type = element["segment_type"]
        text = element["content"].replace(" ", "")
        page_num = element["page_number"]

        if not text:
            continue

        # text修正
        layout_type = layout_map[type]
        if layout_type == "Figure":
            text = "<image>"
        elif layout_type == "Table":
            # text = element["content"].replace(" ", "|")
            text = element["markdown"].replace(" ", "").replace("||", "|").replace("|\n", "")[1:]
            print()

        node_info = {
            "type": type,
            "layout_type": layout_type,
            "order_num": element["segment_id"],
            "text": text.strip(),
            "page_num": page_num - 1,
            # "element": tree.get("element", {})
        }
        nodes.append(node_info)

    return nodes


def tree2list_surya(file_name, parser_json):

    """
    Caption 、
    Footnote 、
    Formula 、
    List-item 、
    Page-footer 、
    Page-header 、
    Picture 、
    Figure 、
    Section-header 、
    Table 、
    Text 、
    Title
    """

    layout_map = {
        "Caption": "Title",  #
        "Footnote": "FigureNote",  # todo
        "Formula": "Formula",  #
        "List-item": "List",  #
        "Page-footer": "其他—页脚",  #
        "Page-header": "其他—页眉",  #
        "Picture": "Figure",  #
        "Figure": "Figure",  #
        "Section-header": "Title",  # todo
        "Table": "Table",  #
        "Text": "Text",  #
        "Title": "Title",  #
    }

    def bbox_trans_surya2beike(file_name, page_bbox_surya, bbox_surya):
        page_bbox_beike = {
            "《贝壳入职管理制度》5页": [595, 841],
            "《贝壳入职管理制度》": [595, 841],
            "《贝壳离职管理制度V3.0》": [595, 841],
            "《贝壳离职管理制度V3.0》5页": [595, 841],
            "中文论文Demo中文文本自动校对综述_4页": [595, 841],
            "自制_4页": [595, 841],
            "花桥学院业务核算指引_6页": [595, 841],
            "英文论文Demo_前3页": [595, 841],
            "评测文件9-博学_13页": [595, 841],
        }

        width_surya = page_bbox_surya[2]
        height_surya = page_bbox_surya[3]

        bbox_beike = [
            bbox_surya[0] / width_surya * page_bbox_beike[file_name][0],
            bbox_surya[1] / height_surya * page_bbox_beike[file_name][1],
            bbox_surya[2] / width_surya * page_bbox_beike[file_name][0],
            bbox_surya[3] / height_surya * page_bbox_beike[file_name][1],
        ]

        return bbox_beike

    # 生成一个主键
    def unique_id_generator():
        id = 1
        while True:
            yield str(id)
            id += 1

    order_num = unique_id_generator()

    nodes = []
    for page_num, page in enumerate(parser_json):
        bboxes = page["bboxes"]
        image_bbox = page["image_bbox"]

        for block in page["bboxes"]:
            if block["label"] not in layout_map:
                print("not in layout_map")
                print(block["label"])
                raise

            if block["label"] in ["Page-footer", "Page-header"]:
                continue

            node_info = {
                "page_num": page_num,  # 从0开始
                "order_num": next(order_num),
                "layout_type": layout_map[block["label"]],
                "type": block["label"],
                "bbox": bbox_trans_surya2beike(file_name, image_bbox, block["bbox"]),
            }
            nodes.append(node_info)

    return nodes


def tree2list_label(order_num, tree):
    """遍历树并返回所有节点的路径和文本"""
    nodes = []
    if tree.get("element"):
        node = tree
        layout_type = node.get("element", {}).get("block_type")
        bbox = node.get("element", {}).get("bbox")
        page_num = node.get("element", {})["page_num"][0]
        node_type = block_type_mapping[layout_type]

        if node_type == "text":
            text = node.get("element", {}).get("text", "").replace(" ", "")
        elif node_type == "table":
            rows = node.get("element", {}).get("rows", [])
            text = "|".join(cell["text"] for row in rows for cell in row.get("cells")).replace(" ", "")
        elif node_type == "image":
            text = "<image>"
        else:
            text = ""
            print("有其他类型的节点:", node_type)
            raise

        node_info = {
            "block_type": node_type,
            "layout_type": layout_type,
            "order_num": order_num,
            "text": text.replace(" ", ""),
            "page_num": page_num,
            "bbox": bbox,
        }
        nodes.append(node_info)
    for order_num, child in tree.get("children", {}).items():
        nodes.extend(tree2list_label(order_num, child))
    return nodes


def clean_text(text):
    # 去除空格、制表符、换行符
    text = re.sub(r'\s+', '', text)
    # 判断是否目录，类似于"..........100"
    pattern = re.compile(r'(.)\1{9,}')
    if bool(pattern.search(text)):
        text = re.sub(r'\.{2,}', '<目录体中连续点点点>', text)
        print(text)

    return text


def find_mapping(logger_badcase, file_name, parser_nodes_ori, label_nodes_ori):
    """找到两棵树之间的映射关系"""
    parser_nodes = copy.deepcopy(parser_nodes_ori)
    label_nodes = copy.deepcopy(label_nodes_ori)
    print("label节点个数：", len(label_nodes))
    edit_dist_1v1_nodes = []
    see_1v1 = []

    mapping = defaultdict(list)

    label_nodes_badcase = copy.deepcopy(label_nodes)

    for label_node in label_nodes:
        if label_node["order_num"] in mapping:
            print(label_node["order_num"])
            print("label有重复的order_num")
            raise
        mapping[label_node["order_num"]] = []

        # 清洗lable_text
        lable_text = clean_text(label_node["text"])
        lable_page = label_node["page_num"]
        for parser_node in parser_nodes:
            # 清洗parser_text
            parser_text = clean_text(parser_node["text"])
            parser_page = parser_node["page_num"]
            if lable_page != -1 and parser_page != -1 and lable_page != parser_page:  # label页码如果标记为-1，即可此处不做页码限制
                continue
            edit_dist = round(edit_distance(lable_text, parser_text), 2)
            if edit_dist >= 0.8:  # 编辑距离在2以内
                mapping[label_node["order_num"]].append(parser_node["order_num"])
                edit_dist_1v1_nodes.append(edit_dist)
                see_1v1.append((lable_text, parser_text))
                parser_nodes.remove(parser_node)
                label_nodes_badcase.remove(label_node)
                break
            elif lable_text in parser_text:
                mapping[label_node["order_num"]].append(parser_node["order_num"])
            elif parser_text in lable_text:  # 包含关系
                # lable_text = lable_text.replace(parser_text, "")
                mapping[label_node["order_num"]].append(parser_node["order_num"])
            else:
                continue

    print("1v1节点个数：", len(edit_dist_1v1_nodes))

    if edit_dist_1v1_nodes:
        print("1v1节点编辑距离：", round(mean(edit_dist_1v1_nodes), 4))
    else:
        print("未找到任何1v1节点")
    edit_dist_all_nodes = copy.deepcopy(edit_dist_1v1_nodes)
    edit_dist_all_nodes.extend([0] * (len(label_nodes) - len(edit_dist_1v1_nodes)))
    print("所有节点编辑距离：", round(mean(edit_dist_all_nodes), 4))

    # 打印badcase
    if logger_badcase:
        logger_badcase.info("*"*100+"文件分隔")
        logger_badcase.info("*"*50+"block切分 badcase：")
        logger_badcase.info(f"\nfile_name: {file_name}\nblock切分 badcase count: {len(label_nodes_badcase)}\n")
        logger_badcase.info("badcase明细如下：")
        for item in label_nodes_badcase:
            order_num_str = item["order_num"]
            text_str = item["text"]
            logger_badcase.info(f"------------------------\n\nfile_name: {file_name}\norder_num: {order_num_str}")
            logger_badcase.info(f"{text_str}\n")

    if len(mapping) != len(edit_dist_all_nodes):
        raise
    return dict(mapping), edit_dist_all_nodes


def calculate_box_relationship(label_node, parser_node):
    bbox1 = label_node["bbox"]
    bbox2 = parser_node["bbox"]
    if not bbox1 or not bbox2:
        raise

    # 创建两个矩形
    label_box = box(bbox1[0], bbox1[1], bbox1[2], bbox1[3])
    parse_box = box(bbox2[0], bbox2[1], bbox2[2], bbox2[3])

    # 计算交集和并集
    intersection = label_box.intersection(parse_box)
    union = label_box.union(parse_box)

    # 计算面积
    inter_area = intersection.area
    union_area = union.area

    if not inter_area:
        return "无重叠"
    elif inter_area / union_area > 0.60:
        return "基本吻合"
    else:
        return "检测框太小"


def find_mapping_by_bbox(logger_badcase, file_name, parser_nodes_ori, label_nodes_ori):
    parser_nodes = copy.deepcopy(parser_nodes_ori)
    label_nodes = copy.deepcopy(label_nodes_ori)
    mapping = defaultdict(list)
    mapping_ref = defaultdict(list)
    aim_page_num = 0

    for label_node in label_nodes:
        label_page_num = label_node["page_num"]
        if aim_page_num != label_page_num:
            print("开启新地一页-----------------------------------------")
            aim_page_num = label_page_num
        mapping[label_node["order_num"]] = []
        mapping_ref[str(label_node["page_num"])+label_node["text"]] = []

        for parser_node in parser_nodes:
            parse_page_num = parser_node["page_num"]
            if label_page_num != parse_page_num:
                continue

            relationship = calculate_box_relationship(label_node, parser_node)

            parse_order_num = parser_node["order_num"]
            label_text = label_node["text"]

            if relationship == "基本吻合":
                print(f"surya框{parse_order_num},基本吻合,文字:{label_text}")
                mapping[label_node["order_num"]] = [parser_node["order_num"]]
                mapping_ref[str(label_node["page_num"])+label_node["text"]] = [parser_node["order_num"]]
                break
            if relationship == "检测框覆盖":
                # 检测框覆盖，可以直接得出解析的元素类型
                print(f"surya框{parse_order_num},检测框覆盖,文字:{label_text}")
                mapping[label_node["order_num"]].append(parser_node["order_num"])
                mapping_ref[str(label_node["page_num"])+label_node["text"]].append(parser_node["order_num"])

                continue
            elif relationship == "检测框太小":
                # 检测框太小，可能该block有多个检测结果
                print(f"surya框{parse_order_num},检测框太小,文字:{label_text}")
                mapping[label_node["order_num"]].append(parser_node["order_num"])
                mapping_ref[str(label_node["page_num"])+label_node["text"]].append(parser_node["order_num"])

                continue

    for text, value_list in mapping_ref.items():
        print("\nlabel块：")
        print(text)
        print("检测框:")
        print(value_list)
    return mapping


def get_node_info(label_nodes, index):
    for label_node in label_nodes:
        if label_node["order_num"] == index:
            return label_node
    else:
        raise


def evaluate_layout(mapping, label_nodes, parser_nodes):
    count_all = len(label_nodes)

    confusion_matrix = pd.DataFrame(0, index=["label_" + i for i in block_type],
                                    columns=[parse_str + i for i in block_type] + ["p_0", "p_N"])

    for lable_index, parser_index_list in mapping.items():
        layout_right_list = []
        label_node = get_node_info(label_nodes, lable_index)
        layout_type = label_node["layout_type"]

        if len(parser_index_list) == 1:
            parser_node = get_node_info(parser_nodes, parser_index_list[0])
            confusion_matrix.loc["label_" + layout_type, parse_str + parser_node["layout_type"]] += 1

            if layout_type == parser_node["layout_type"]:
                print("【1v1 right】label:", layout_type, "parse:", parser_node["layout_type"],
                      label_node["text"])
            else:
                print("【1v1 wrong】label:", layout_type, "parse:", parser_node["layout_type"],
                      label_node["text"])

        elif len(parser_index_list) > 1:
            print("【1vN find】label:", len(parser_index_list))
            for parser_index in parser_index_list:
                parser_node = get_node_info(parser_nodes, parser_index)
                if layout_type == parser_node["layout_type"]:
                    layout_right_list.append(label_node)
                    print("【1vN right】label:", layout_type, "parse:", parser_node["layout_type"], parser_node.get("text"))
                else:
                    print("【1vN wrong】label:", layout_type, "parse:", parser_node["layout_type"], parser_node.get("text"))

            acc = len(layout_right_list) * 1.0 / len(parser_index_list)
            confusion_matrix.loc["label_" + layout_type, parse_str + parser_node["layout_type"]] += acc
            confusion_matrix.loc["label_" + layout_type, "p_N"] += (1.0 - acc)

        else:  # len(parser_index_list) = 0
            confusion_matrix.loc["label_" + layout_type, "p_0"] += 1
            print("【1v0 wrong】label:", layout_type, label_node["text"])

        # 检查

    # 打印表格
    print(confusion_matrix.to_string())

    return confusion_matrix

    # print("节点总数：", count_all)
    # print("版面识别正确个数：", len(layout_right_list))


def label_tree_add_bbox(order_num, beike_parser_nodes, label_tree, mapping):
    element = label_tree.get("element", {})
    child = label_tree.get("child", {})

    # 处理element
    if element:
        element["bbox"] = []

        # 找到对应的节点
        if len(mapping.get(order_num)) == 1:
            order_num_beike = mapping.get(order_num)[0]
            # 找到bbox
            for node in beike_parser_nodes:
                if node["order_num"] == order_num_beike:
                    if (
                            element.get("text") and node.get("text")
                            and (element["text"].strip().replace(" ", "").replace("-", "") != node["text"].strip().replace(" ", "").replace("-", ""))
                    ):
                        print("文字不完全相同")
                        print("parse:" + node["text"].strip().replace(" ", "").replace("-", ""))
                        print("label:" + element["text"].strip().replace(" ", "").replace("-", ""))
                        print("")
                        element["bbox_need_check"] = ""

                    element["bbox"] = node["bbox"]
                    break

    # 处理child
    for child_order_num, data in child.items():
        label_tree_add_bbox(str(child_order_num), beike_parser_nodes, data, mapping)

    return


def surya_nodes_add_bbox(order_num, beike_parser_nodes, label_tree, mapping):
    element = label_tree.get("element", {})
    child = label_tree.get("child", {})

    # 处理element
    if element:
        element["bbox"] = []

        # 找到对应的节点
        if len(mapping.get(order_num)) == 1:
            order_num_beike = mapping.get(order_num)[0]
            # 找到bbox
            for node in beike_parser_nodes:
                if node["order_num"] == order_num_beike:
                    if (
                            element.get("text") and node.get("text")
                            and (element["text"].strip().replace(" ", "").replace("-", "") != node["text"].strip().replace(" ", "").replace("-", ""))
                    ):
                        print("文字不完全相同")
                        print("parse:" + node["text"].strip().replace(" ", "").replace("-", ""))
                        print("label:" + element["text"].strip().replace(" ", "").replace("-", ""))
                        print("")
                        element["bbox_need_check"] = ""

                    element["bbox"] = node["bbox"]
                    break

    # 处理child
    for child_order_num, data in child.items():
        label_tree_add_bbox(str(child_order_num), beike_parser_nodes, data, mapping)

    return


def evaluation_single(logger_badcase, file_name, parser=""):
    print("评测文件：", file_name)
    print("评测引擎：", parser)

    # 解析结果获取
    if parser == "beike":
        parser_json = load_json(f"parse_json/{parser}/" + file_name + '.json')
        parser_nodes = tree2list_beike(parser_json["root"])
        pc_edges_parser = get_pc_edges_beike("", parser_json["root"]["child"])
        print()
    elif parser == "ali":
        parser_json = load_json(f"parse_json/{parser}/" + file_name + '_result_ali.json')
        parser_nodes = tree2list_ali(parser_json)
        pc_edges_parser = get_pc_edges_ali(parser_json)
    # elif parser == "adobe":
    #     parser_json = load_json("adobe/structuredData" + file_name + '_chi.json')
    #     parser_nodes = tree2list_adobe(parser_json)
    elif parser == "unstructured":
        parser_json = load_json(f"parse_json/{parser}/" + file_name + '.json')
        parser_nodes = tree2list_unstructured(parser_json)
        pc_edges_parser = get_pc_edges_unstructured(parser_json)
    elif parser == "chunkr":
        parser_json = load_json(f"parse_json/{parser}/" + file_name + '.json')
        parser_nodes = tree2list_chunkr(parser_json)
        pc_edges_parser = {}
    elif parser == "paoding":
        parser_json = load_json(f"parse_json/{parser}/" + file_name + '.json')
        parser_nodes = tree2list_paoding(parser_json)
        pc_edges_parser = get_pc_edges_paoding(parser_json)
    elif parser == "llamaparse":
        parser_nodes = load_markdown(f"parse_json/{parser}/" + file_name + '.pdf.md')
        pc_edges_parser = get_pc_edges_llamaparse(parser_nodes)
    elif parser == "docling":
        parser_nodes = load_markdown(f"parse_json/{parser}/" + file_name + '.md')
        pc_edges_parser = get_pc_edges_llamaparse(parser_nodes)
    elif parser == "mineru":
        parser_nodes = load_markdown(f"parse_json/{parser}/" + file_name + '.md')
        pc_edges_parser = get_pc_edges_llamaparse(parser_nodes)
    elif parser == "microsoft":
        parser_nodes = load_markdown(f"parse_json/{parser}/" + file_name + '.pdf.md')
        pc_edges_parser = get_pc_edges_llamaparse(parser_nodes)
    else:
        raise "未实现的解析引擎"

    # 标注结果获取
    label_tree = load_json("label_json/" + file_name + '_GT_label.json')
    label_nodes = tree2list_label("1", label_tree["root"])
    label_order2text_dic = get_order2text(label_nodes)
    # 父子边
    pc_edges_label = get_pc_edges_label("root", label_tree["root"])


    # 映射关系 和 block切分正确率
    mapping, edit_dist_all_nodes = find_mapping(logger_badcase, file_name, parser_nodes, label_nodes)
    mapping = dict(sorted(mapping.items(), reverse=False))
    # print(json.dumps(mapping, indent=2, ensure_ascii=False))

    # 版面元素正确率
    confusion_matrix = evaluate_layout(mapping, label_nodes, parser_nodes)

    # 层级关系正确率
    struct_right_cnt, struct_all_count, right_mapping, error_mapping = cal_structure_accuracy(pc_edges_label, pc_edges_parser, mapping, file_name)

    # 打印层级badcase
    logger_badcase.info("*"*50+"层级badcase(未找到的父子关系)：")
    logger_badcase.info(f"\nfile_name: {file_name}\n层级 badcase count: {len(error_mapping)}\n")
    logger_badcase.info("badcase明细如下：")
    for k, v in error_mapping.items():
        logger_badcase.info(f"------------------------\n\nfile_name: {file_name}")
        logger_badcase.info(k+"的父节点"+v)
        logger_badcase.info("\n父亲：")
        logger_badcase.info(label_order2text_dic[v])
        logger_badcase.info("\n孩子：")
        logger_badcase.info(label_order2text_dic[k])
        logger_badcase.info("")

    return confusion_matrix, edit_dist_all_nodes, mapping, struct_right_cnt, struct_all_count, right_mapping, error_mapping


# 通过order获取text
def get_order2text(label_nodes):
    label_order2text_dic = {}
    for label_node in label_nodes:
        label_order2text_dic[label_node["order_num"]] = label_node["text"]
    return label_order2text_dic


def cal_structure_accuracy(pc_edges_label, pc_edges_parser, mapping, file_name):
    right_mapping = {}
    error_mapping = {}
    all_count = len(pc_edges_label)
    right_cnt = 0
    error_cnt = 0
    for child, father in pc_edges_label.items():
        child_map = mapping.get(child, [])
        father_map = mapping.get(father, [])
        if (len(child_map) == 1 and len(father_map) == 1) and pc_edges_parser.get(child_map[0]) == father_map[0]:
            right_cnt += 1
            right_mapping[file_name+child] = father
        else:
            error_cnt += 1

            error_mapping[child] = father

    print(f"\n结构准确率:{right_cnt * 1.0 / all_count:.2f}  ({right_cnt} / {all_count})  {file_name}")

    return right_cnt, all_count, right_mapping, error_mapping


def get_pc_edges_beike(order_num_father, data):
    pc_edges = {}
    for item in data:
        order_num_child = item["order_num"]
        child_list = item["child"]
        if order_num_father:
            pc_edges[order_num_child] = order_num_father
        pc_edges_item = get_pc_edges_beike(order_num_child, child_list)
        pc_edges.update(pc_edges_item)

    return pc_edges


def get_pc_edges_ali(parser_json):
    pc_edges = {}
    data = parser_json["logics"]["docTree"]
    for item in data:
        father = item["backlink"]["上级"][0]
        child = item["uniqueId"]
        # if
        pc_edges[child] = father
    return pc_edges


def get_pc_edges_unstructured(parser_json):
    pc_edges = {}
    data = parser_json
    for item in data:
        if item["metadata"].get("parent_id"):
            father = item["metadata"]["parent_id"]
            child = item["element_id"]
            pc_edges[child] = father
    return pc_edges


def get_pc_edges_paoding(parser_json):
    pc_edges = {}
    data = parser_json["syllabus"]["children"]

    def record_relationship(father, children_range):
        form_child = children_range[0]
        to_child = children_range[1]
        children_list = list(range(form_child, to_child))
        for i in children_list:
            if str(i) != str(father) and str(i) not in pc_edges:
                pc_edges[str(i)] = str(father)

    def get_pc_edge_recursive(father, children):

        # 先记录所有list中第一个元素的父节点
        if father:
            for child in children:
                if str(child["range"][0]) not in pc_edges:
                    pc_edges[str(child["range"][0])] = str(father)

        print()
        for item in children:
            # 如果没有children直接记录
            if not item["children"]:
                # 例如：  29   [29:32]   先记录30、31的父节点29
                record_relationship(item["element"], item["range"])

            else:
                get_pc_edge_recursive(item["element"], item["children"])
                record_relationship(item["element"], item["range"])

    get_pc_edge_recursive(None, data)

    pc_edges_order = dict(sorted(pc_edges.items(), key=lambda item: int(item[0])))

    return pc_edges_order


def get_pc_edges_llamaparse(parser_json):
    pc_edges_parser = {}
    father = ""

    for node in parser_json:
        if node["type"] == "Title":
            father = node["order_num"]
        elif father:
            pc_edges_parser[node["order_num"]] = father
    return pc_edges_parser


def get_pc_edges_label(order_num, label_tree):
    pc_edges = {}
    child = label_tree.get("child", {})

    for order_num_child, data in child.items():
        if order_num != "root":
            pc_edges[order_num_child] = order_num
        pc_edges_item = get_pc_edges_label(order_num_child, data)
        pc_edges.update(pc_edges_item)

    return pc_edges


def cal_accuracy(confusion_matrix):
    # 计算每个标签的准确率
    accuracies = {}
    total_correct = 0
    total_elements = 0

    print("每个标签的准确率：")
    for label in confusion_matrix.index:
        correct = confusion_matrix.loc[label, label.replace('label_', parse_str)]
        total = confusion_matrix.loc[label].sum()
        accuracy = correct / total if total > 0 else 0
        # print(label.replace('label_', '') + "\t: ", f"{accuracy:.2f} ({correct}/{total})")
        print(f"{accuracy:.2f}  ({correct:.1f} / {total:.0f})")
        accuracies[label] = accuracy
        total_correct += correct
        total_elements += total

    # 计算总的准确率
    overall_accuracy = total_correct / total_elements

    logger.info(f"\n版面元素准确率：\t\t{overall_accuracy:.2f}  ({total_correct:.1f} / {total_elements:.0f})")


def generate_report():
    for parser in parser_list:
        logger.info(f"评测引擎:{parser}")
        logger.info(f"------------------")
        evaluation(parser)


def main():
    beike_parse_output.parse()  # 如果不需要重新解析，可以注掉这行
    generate_report()


def label_json_add_bbox_by_beike_parse():

    for file_name in file_list:
        # 解析结果
        parser_json = load_json(f"parse_json/beike/" + file_name + '_beike.json')
        parser_nodes = tree2list_beike(parser_json["root"])

        # 标注结果
        label_tree = load_json("label_json/" + file_name + '_GT_label.json')
        label_nodes = tree2list_label("1", label_tree["root"])

        # 映射关系
        mapping, edit_dist_all_nodes = find_mapping("", file_name, parser_nodes, label_nodes)
        mapping = dict(sorted(mapping.items(), reverse=False))

        label_tree_add_bbox("root", parser_nodes, label_tree["root"], mapping)
        beike_parse_output.output(label_tree, file_name, "evaluation/label_json/", "_GT_label.json")


def evaluation_surya():
    confusion_matrix_list = []

    for file_name in file_list:
        print("evaluation_surya begin:" + file_name)
        # 解析结果
        parser_json = load_json(f"parse_json/surya/" + file_name + '.json')
        parser_nodes = tree2list_surya(file_name, parser_json[file_name])

        # 标注结果
        label_tree = load_json("label_json/" + file_name + '_GT_label.json')
        label_nodes = tree2list_label("1", label_tree["root"])
        label_nodes = sorted(label_nodes, key=lambda x: x['page_num'])

        mapping = find_mapping_by_bbox("", file_name, parser_nodes, label_nodes)
        mapping = dict(sorted(mapping.items(), reverse=False))
        # print(json.dumps(mapping, indent=2, ensure_ascii=False))

        new_dict = get_revers_map(mapping)
        print("surya统计：")
        print(len(label_nodes))
        print(len([1 for k, v in new_dict.items() if len(v) == 1]))

        # 版面元素正确率
        confusion_matrix = evaluate_layout(mapping, label_nodes, parser_nodes)
        confusion_matrix_list.append(confusion_matrix)

    total_confusion_matrix = sum(confusion_matrix_list)
    print(total_confusion_matrix.to_string())

    # 每种类型的准确率
    cal_accuracy(total_confusion_matrix)


def get_revers_map(original_dict):
    original_dict = {k: v for k, v in original_dict.items() if len(v) == 1}

    # 新的字典
    new_dict = {}
    # 遍历原始字典
    for key, values in original_dict.items():
        for value in values:
            if value in new_dict:
                new_dict[value].append(key)
            else:
                new_dict[value] = [key]

    new_dict = {k: v for k, v in new_dict.items() if len(v) == 1}
    return new_dict

# def surya_json_add_beike_bbox():
#     for file_name in file_list:
#         # 解析结果
#         parser_json = load_json(f"parse_json/surya/" + file_name + '.json')
#         parser_nodes = tree2list_surya(file_name, parser_json[file_name])
#
#         # 标注结果
#         label_tree = load_json("label_json/" + file_name + '_GT_label.json')
#         label_nodes = tree2list_label("1", label_tree["root"])
#
#         mapping = find_mapping_by_bbox("", file_name, parser_nodes, label_nodes)
#         mapping = dict(sorted(mapping.items(), reverse=False))
#         # print(json.dumps(mapping, indent=2, ensure_ascii=False))


# 输surya识别layout之后的pdf预览
def surya_view():
    for file_name in file_list:
        # 解析结果
        parser_json = load_json(f"parse_json/surya/" + file_name + '.json')
        parser_nodes = tree2list_surya(file_name, parser_json[file_name])

        debug_file = fitz.Document(f"documents/" + file_name + '.pdf')
        debug_pages = [page for page in debug_file.pages()]
        for parse_node in parser_nodes:
            order_num = parse_node["order_num"]
            page_num = parse_node["page_num"]
            bbox = parse_node["bbox"]
            layout_type = parse_node["layout_type"]
            draw_text = f"{order_num} {layout_type}"
            draw_box(debug_pages[page_num], draw_text, fitz.Rect(bbox))
        debug_file.save(f"documents/" + file_name + '_surya_ori.pdf')


def draw_box(page, name, bbox):
    white = (255 / 255, 255 / 255, 255 / 255)
    black = (0 / 255, 0 / 255, 0 / 255)

    # Page画框框
    page.draw_rect(bbox, color=(0, 0, 0), fill=None, width=0.5, dashes=None, overlay=True, fill_opacity=0.5)
    # Page画名字的框框
    page.draw_rect((bbox.x0, bbox.y0 - 8, bbox.x0 + len(name)*5.5, bbox.y0), color=black, fill=black, overlay=True)
    # Page画名字的text
    page.insert_text((bbox.x0, bbox.y0), name, color=white)


def evaluation(parser_name):

    confusion_matrix_list = []
    edit_dist_allfile = []
    edit_dist_allfile2 = []

    count_1v1 = 0
    count_1vm = 0
    count_nomap = 0

    struct_right_cnt = 0
    struct_all_count = 0
    struct_mapping = {}

    logger_badcase = log_setting("reports/" + parser_name + "/badcase_" + datetime.datetime.now().strftime('%Y%m%d_%H点%M分') + ".txt")

    for file_name in file_list:
        confusion_matrix, edit_dist_file_nodes, mapping, right_cnt, all_count, right_mapping, error_mapping = \
            (evaluation_single(logger_badcase, file_name, parser_name))

        confusion_matrix_list.append(confusion_matrix)
        edit_dist_allfile.extend(edit_dist_file_nodes)
        edit_dist_allfile2.append(edit_dist_file_nodes)

        count_1v1 += len([v for k, v in mapping.items() if len(v) == 1])
        count_1vm += len([v for k, v in mapping.items() if len(v) > 1])
        count_nomap += len([v for k, v in mapping.items() if len(v) == 0])
        struct_right_cnt += right_cnt
        struct_all_count += all_count
        struct_mapping.update(right_mapping)

    total_confusion_matrix = sum(confusion_matrix_list)
    print("total_confusion_matrix.to_string()")
    print(total_confusion_matrix.to_string())

    # logger.info(f"总节点数：{len(edit_dist_allfile)}")
    # logger.info(f"1v1映射节点数：{len([x for x in edit_dist_allfile if x > 0])}\n")

    real_1v1_count = len([x for x in edit_dist_allfile if x > 0])  # 这里是指相似度大于0.8的节点；目标映射数为1并不是真正的相似度大于0.8

    logger.info(f"\nblock切分准确率：\t\t{mean(edit_dist_allfile):.2f}  ({real_1v1_count} / {len(edit_dist_allfile)})")
    # 每种类型的准确率
    cal_accuracy(total_confusion_matrix)

    # print("找到的父子节点：")
    # for k, v in struct_mapping.items():
    #     print(k+"的父节点"+v)


    # print("全部文档非1v1映射节点数：", len([x for x in edit_dist_allfile if x == 0]))

    # print("全部文档1v1映射节点数：", count_1v1)
    # print("全部文档多映射节点数：", count_1vm)
    # print("全部文档无映射节点数：", count_nomap)
    logger.info(f"\n层级结构准确率：\t\t{struct_right_cnt * 1.0 / struct_all_count:.2f}  ({struct_right_cnt} / {struct_all_count})\n\n")


if __name__ == "__main__":
    logger_tmp = log_setting("reports/tmp.txt")

    # 单个文件 ---------------------------------------------------
    # evaluation_single(logger_tmp, "《贝壳入职管理制度》5页", "beike")
    # evaluation_single(logger_tmp, "《贝壳入职管理制度》5页", "ali")
    #
    # evaluation_single(logger_tmp, "《贝壳离职管理制度V3.0》5页", "beike")
    # evaluation_single(logger_tmp, "《贝壳离职管理制度V3.0》5页", "ali")
    # evaluation_single(logger_tmp, "《贝壳离职管理制度V3.0》5页", "unstructured")
    #
    # evaluation_single(logger_tmp, "中文论文Demo中文文本自动校对综述_4页", "beike")
    # evaluation_single(logger_tmp, "中文论文Demo中文文本自动校对综述_4页", "ali")
    #
    # evaluation_single(logger_tmp, "自制_4页", "beike")
    # evaluation_single(logger_tmp, "自制_4页", "ali")
    #
    # evaluation_single(logger_tmp, "花桥学院业务核算指引_6页", "beike")
    # evaluation_single(logger_tmp, "花桥学院业务核算指引_6页", "ali")
    #
    # evaluation_single(logger_tmp, "英文论文Demo_前3页", "beike")
    # evaluation_single(logger_tmp, "英文论文Demo_前3页", "ali")
    #
    # evaluation_single(logger_tmp, "评测文件9-博学_13页", "beike")
    # evaluation_single(logger_tmp, "评测文件9-博学_13页", "ali")

    main()

    # label_json_add_bbox_by_beike_parse  # 根据贝壳解析结果给label添加bbox的（影响大，不要随意执行）
    # surya_json_add_beike_bbox()  # 添加转化后的bbox

    # evaluation_surya()
    # surya_view()  # surya看效果

    # 说明：运行该文件会直接输出最新的评测指标到reports/output_indicators文件中
    # 步骤：
    # 1、使用贝壳解析引擎，解析评测集中的8个文件
    # 2、通过贝壳以及待评测的解析引擎的结果，输出评测指标
