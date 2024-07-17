# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/7/17
#    @Description   : 
#
# ===============================================================
import io
import json
from io import BytesIO

from docx import Document, ImagePart
from docx.oxml import CT_Picture
from docx.text.paragraph import Paragraph

from server import s3_service
from server import utils
from server.constants import IMAGE, TEXT, TABLE


def find_image(doc: Document, paragraph: Paragraph):
    img = paragraph._element.xpath('.//pic:pic')
    if not img:
        return
    img: CT_Picture = img[0]
    embed = img.xpath('.//a:blip/@r:embed')[0]
    related_part: ImagePart = doc.part.related_parts[embed]
    image = related_part.image
    return image


def build_image_item(image_blob):
    filename = IMAGE + utils.get_random_name()
    image_s3_url = s3_service.s3_upload(filename=filename, data=BytesIO(image_blob))
    return dict(text=image_s3_url, type=IMAGE)


def layout_parse(file):
    layouts = []

    file_stream = io.BytesIO(file)
    doc = Document(file_stream)

    for element in doc.element.body:
        try:
            if element.tag.endswith('p'):
                # 处理段落
                paragraph = doc.paragraphs[doc.element.body.index(element)]
                text = paragraph.text
                if text.strip():  # 忽略空段落
                    layouts.append(dict(text=text, type=TEXT))

                # 检查段落中的图片
                image = find_image(doc, paragraph)
                if image is not None:
                    layouts.append(build_image_item(image.blob))
            elif element.tag.endswith('tbl'):
                # 处理表格
                table = element
                table_text = ""
                for row in table.findall('.//w:tr', doc.element.nsmap):
                    for cell in row.findall('.//w:tc', doc.element.nsmap):
                        table_text = " | ".join([table_text, next(cell.itertext(), '')])
                if table_text:
                    layouts.append(dict(text=table_text, type=TABLE))
        except Exception as e:
            print(f"处理元素时出错，type: {element}，errmsg：{str(e)}")
            continue

    return layouts


if __name__ == "__main__":

    file_name = '/Users/lucio/code/others/工作内容/工作内容2024/0709多文件类型解析代码调研/demo_image.docx'

    # 读取本地文件
    try:
        with open(file_name, 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        print(f"读取文件失败: {e}")

    print(json.dumps(layout_parse(buf_data), ensure_ascii=False))
