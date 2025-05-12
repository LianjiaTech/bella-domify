from pdf2docx import Converter
from server.context import user_context, DEFAULT_USER

test_dir = '/Users/beike/Documents/工作记录/智能架构/2024/知识库/结构化提取/'
file_name = '评测文件9-博学_13页.pdf'
converter = Converter(test_dir + file_name)
user_context.set(DEFAULT_USER)

dom_tree = converter.dom_tree_parse(
    start=3, end=4,
    remove_watermark=True,
    debug=True,
    debug_file_name=test_dir + "结果/" + file_name,
    parse_stream_table=False
)
