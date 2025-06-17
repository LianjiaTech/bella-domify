# ===========================
# 流程文档
# https://doc.weixin.qq.com/doc/w3_AOsASwZXANEuo8cdrbvS16KPAnJCD?scode=AJMA1Qc4AAw6bV1mLrAOsASwZXANE
# ===========================
import json
import os

from pdf2docx import Converter
from pdf2docx.dom_tree.domtree import DomTreeModel
from server.context import user_context

os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"

user_context.set("1000000020353701")

test_dir = "test_document/"


def pdf_parser(file_name: str, debug: bool = False) -> dict:
    converter = Converter(test_dir + f"{file_name}.pdf")
    dom_tree = converter.dom_tree_parse(
        start=0, end=4,
        remove_watermark=True,
        debug=debug,
        debug_file_name=test_dir + f"{file_name}-debug.pdf",
        parse_stream_table=False,
        filter_cover=True,
    )
    if debug:
        with open(test_dir + f"{file_name}-debug.json", "w") as fw:
            json.dump(DomTreeModel(dom_tree=dom_tree).model_dump(), fw, ensure_ascii=False, indent=2)
    return DomTreeModel(dom_tree=dom_tree).model_dump()


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
