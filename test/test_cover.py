# ===========================
# 流程文档
# https://doc.weixin.qq.com/doc/w3_AOsASwZXANEuo8cdrbvS16KPAnJCD?scode=AJMA1Qc4AAw6bV1mLrAOsASwZXANE
# ===========================
import json
import os

from doc_parser.dom_parser.domtree.domtree import DomTreeModel
from doc_parser.dom_parser.parsers.pdf.converter import PDFConverter
from test import TEST_PATH


def pdf_parser(file_name: str, debug: bool = False) -> dict:
    converter = PDFConverter(os.path.join(TEST_PATH, "samples", f"{file_name}.pdf"))
    dom_tree = converter.dom_tree_parse(
        start=0, end=4,
        remove_watermark=True,
        debug=debug,
        debug_file_name=os.path.join(TEST_PATH, "samples", f"{file_name}-debug.pdf"),
        parse_stream_table=False,
        filter_cover=True,
    )
    if debug:
        with open(os.path.join(TEST_PATH, "samples", f"{file_name}-debug.json", "w")) as fw:
            json.dump(dom_tree.model_dump(), fw, ensure_ascii=False, indent=2)
    return dom_tree.model_dump()


def test_cover():
    result1 = pdf_parser("demo")
    assert result1["root"]["child"][0]["element"]["text"].strip() == "Automated Data Extraction from Scholarly Line"
    result2 = pdf_parser("demo-blank")
    assert len(result2["root"]["child"]) == 0, "Expected no content in the blank PDF"
    result3 = pdf_parser("demo-image")
    assert result3["root"]["child"][0]["element"]["text"].strip() == "A normal image:"
    result4 = pdf_parser("demo-table")
    assert result4["root"]["child"][0]["element"]["text"].strip() == "Text format and Page Layout"
    result5 = pdf_parser("demo-table-nested")
    assert result5["root"]["child"][0]["child"][0]["element"]['block_type'] == 'table'
