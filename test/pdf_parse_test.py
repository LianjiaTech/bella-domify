import os

from doc_parser.dom_parser.parsers.pdf.converter import PDFConverter
from test import TEST_PATH


def test_dom_tree():
    # # 使用项目内的test/document目录
    test_dir = os.path.join(TEST_PATH, "document")
    file_name = '英文论文Demo_前3页.pdf'
    converter = PDFConverter(os.path.join(test_dir, file_name))
    # 将结果保存在test/results目录下
    results_dir = os.path.join(TEST_PATH, 'results')
    # 确保结果目录存在,不存在则创建
    os.makedirs(results_dir, exist_ok=True)

    dom_tree = converter.dom_tree_parse(
        remove_watermark=True,
        debug=True,
        debug_file_name=os.path.join(results_dir, file_name),
        parse_stream_table=False
    )
