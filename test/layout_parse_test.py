import os

from doc_parser.layout_parser.csv_parser import layout_parse as csv_layout_parse
from doc_parser.layout_parser.docx_parser import layout_parse as docx_layout_parse
from doc_parser.layout_parser.pdf_parser import layout_parse as pdf_layout_parse
from doc_parser.layout_parser.pptx_parser import layout_parse as pptx_layout_parse
from doc_parser.layout_parser.txt_parser import layout_parse as txt_layout_parse
from doc_parser.layout_parser.xls_parser import layout_parse as xls_layout_parse
from doc_parser.layout_parser.xlsx_parser import layout_parse as xlsx_layout_parse
from test import TEST_PATH

file_path = os.path.join(TEST_PATH, "samples", "file_type_demo")


def test_csv():
    file_name = 'demo.csv'
    # 读取本地文件
    buf_data = load_test_file(file_name)
    result_json, result_text = csv_layout_parse(buf_data)
    assert result_json is not None, "CSV解析失败，结果为None"
    assert result_text is not None, "CSV解析失败，文本结果为None"


def test_docx():
    file_name = 'demo.docx'
    # 读取本地文件
    buf_data = load_test_file(file_name)
    result_json, result_text = docx_layout_parse(buf_data)
    assert result_json is not None, "DOCX解析失败，结果为None"
    assert result_text is not None, "DOCX解析失败，文本结果为None"


def test_pdf():
    file_name = 'demo.pdf'
    # 读取本地文件
    buf_data = load_test_file(file_name)
    result_json, result_text = pdf_layout_parse(buf_data)
    assert result_json is not None, "PDF解析失败，结果为None"
    assert result_text is not None, "PDF解析失败，文本结果为None"


def test_pptx():
    file_name = 'demo.pptx'
    buf_data = load_test_file(file_name)
    result_json, result_text =  pptx_layout_parse(buf_data)
    assert result_json is not None, "PPTX解析失败，结果为None"
    assert result_text is not None, "PPTX解析失败，文本结果为None"


def test_txt():
    file_name = 'demo.txt'
    buf_data = load_test_file(file_name)
    result_json, result_text =  txt_layout_parse(buf_data)
    assert result_json is not None, "TXT解析失败，结果为None"
    assert result_text is not None, "TXT解析失败，文本结果为None"


def test_xls():
    file_name = 'demo.xls'
    # 读取本地文件
    buf_data = load_test_file(file_name)
    result_json, result_text =  xls_layout_parse(buf_data)
    assert result_json is not None, "XLS解析失败，结果为None"
    assert result_text is not None, "XLS解析失败，文本结果为None"


def test_xlsx():
    file_name = 'demo.xlsx'
    buf_data = load_test_file(file_name)
    result_json, result_text =  xlsx_layout_parse(buf_data)
    assert result_json is not None, "XLSX解析失败，结果为None"
    assert result_text is not None, "XLSX解析失败，文本结果为None"


def load_test_file(file_name):
    # 读取本地文件
    try:
        with open(os.path.join(file_path, file_name), 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        assert False, "读取文件失败"
    return buf_data