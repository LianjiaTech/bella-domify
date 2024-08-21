# ===========================
# 流程文档
# https://doc.weixin.qq.com/doc/w3_AOsASwZXANEuo8cdrbvS16KPAnJCD?scode=AJMA1Qc4AAw6bV1mLrAOsASwZXANE
# ===========================
import os

from pdf2docx import Converter
from pdf2docx.dom_tree.domtree import DomTreeModel
from server.context import user_context

os.environ["OPENAI_API_KEY"] = "<ak>"
os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"

user_context.set("1000000020353701")

test_dir = "../test_document/"


def pdf_parser(file_name: str) -> dict:
    converter = Converter(test_dir + f"{file_name}.pdf")
    dom_tree = converter.dom_tree_parse(
        start=0, end=4,
        remove_watermark=True,
        debug=False,
        debug_file_name="",
        parse_stream_table=False
    )
    return DomTreeModel(dom_tree=dom_tree).model_dump()


def test_cover():
    result1 = pdf_parser("LW2626-01《员工费用报销管理规定》V4.0")
    assert result1["root"]["child"][0]["element"]["text"].strip() == "版本变更记录"
    result2 = pdf_parser("博学_13页")
    assert result2["root"]["child"][0]["element"]["text"].strip() == "�  �"
    result3 = pdf_parser("花桥学院业务核算指引")
    assert result3["root"]["child"][0]["element"]["text"].strip() == "版本变更记录"
    result4 = pdf_parser("新零售品类销售签约规范")
    assert result4["root"]["child"][0]["element"]["text"].strip() == "新零售品类销售签约规范"
    result5 = pdf_parser("FAQ判断case")
    assert result5["root"]["child"][0]["element"]["text"].strip() in ["明白了，以下是整理后的文档:", "### 营销"]


if __name__ == "__main__":
    test_cover()
