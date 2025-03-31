# ===========================
# 流程文档
# https://doc.weixin.qq.com/doc/w3_AOsASwZXANEuo8cdrbvS16KPAnJCD?scode=AJMA1Qc4AAw6bV1mLrAOsASwZXANE
# ===========================
import json
import os

from pdf2docx import Converter
from pdf2docx.dom_tree.domtree import DomTreeModel
from server.context import user_context

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_BASE_URL"] = "https://openapi-ait.ke.com/v1/"

user_context.set("1000000020353701")

test_dir = "../test_document/"


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
    result1 = pdf_parser("LW2626-01《员工费用报销管理规定》V4.0")
    assert result1["root"]["child"][0]["element"]["text"].strip() == "版本变更记录"
    result2 = pdf_parser("博学_13页")
    assert result2["root"]["child"][0]["element"]["text"].strip() == "�  �"
    result3 = pdf_parser("花桥学院业务核算指引")
    assert result3["root"]["child"][0]["element"]["text"].strip() == "版本变更记录"
    result4 = pdf_parser("新零售品类销售签约规范")
    assert result4["root"]["child"][0]["element"]["text"].strip() == "新零售品类销售签约规范"
    result5 = pdf_parser("FAQ判断case")
    assert result5["root"]["child"][0]["child"][0]["element"]["text"].strip() in ["营销激励问题-物品承诺/激励-承诺/激励未兑现-兑换错误"]
    result6 = pdf_parser("奥丁QA")
    assert result6["root"]["child"][0]["child"][0]["element"]["text"].strip() == "如何配置奥丁报告的权限？"
    result7 = pdf_parser("《贝壳入职管理制度》5页")
    assert result7["root"]["child"][0]["element"]["text"].strip() == "为了规范公司新员工的入职管理，明确入职各环节的操作流程的标准化，提高入职手续办理 效率，提供良好的入职办理体验，人力资源共享服务中心特制定本制度，本制度于 2020 年 8 月 11 日生效。"
    result8 = pdf_parser("法式风-法式（2）")
    assert result8["root"]["child"][0]["element"]["text"].strip().startswith("三、法式风")


if __name__ == "__main__":
    test_cover()
