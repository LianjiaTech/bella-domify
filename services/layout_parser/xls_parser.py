# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/11/7
#    @Description   :
#
# ===============================================================
import xlrd
from io import BytesIO
import os


def layout_parse(byte_data):
    # 将字节数据转换为BytesIO对象
    byte_stream = BytesIO(byte_data)

    # 打开XLS文件
    workbook = xlrd.open_workbook(file_contents=byte_stream.read())

    # 用于存储所有内容的字符串
    all_content = ""

    # 遍历每个工作表
    for sheet_index in range(workbook.nsheets):
        worksheet = workbook.sheet_by_index(sheet_index)
        all_content += f"Sheet: {worksheet.name}\n"

        # 遍历每一行
        for row_index in range(worksheet.nrows):
            row = worksheet.row(row_index)
            # 遍历每一列
            for cell in row:
                # 将单元格的值拼接到字符串中
                all_content += str(cell.value) + "\t"
            all_content += "\n"
        all_content += "\n"

    result_text = all_content
    result_json = all_content
    return result_json, result_text


if __name__ == "__main__":

    file_path = os.path.abspath(__file__).split("document_parse")[0] + "document_parse/test/samples/file_type_demo/"

    file_name = 'demo.xls'

    # 读取本地文件
    try:
        with open(file_path + file_name, 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        print(f"读取文件失败: {e}")

    print(layout_parse(buf_data))
