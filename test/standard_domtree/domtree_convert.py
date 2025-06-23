import json
import os
import uuid

from fastapi.encoders import jsonable_encoder

from doc_parser.dom_parser.converter import Converter
from doc_parser.dom_parser.domtree.domtree import DomTreeModel
from server.protocol.standard_domtree import StandardDomTree, SourceFile
from test import TEST_PATH

file_path = os.path.join(TEST_PATH, "document")



def test_domtree_convert():
    file_name = '英文论文Demo_前3页.pdf'
    # 读取本地文件
    converter = Converter(os.path.join(file_path, file_name))
    dom_tree = converter.dom_tree_parse(
        start=0, end=3,
        remove_watermark=True,
        debug=False,
        debug_file_name=os.path.join(file_path, file_name),
        parse_stream_table=False
    )
    file_info = {
        "id": uuid.uuid4().hex,
        "filename": file_name,
        "type": "pdf",
        "mime_type": "application/pdf"
    }
    dom_tree_json = jsonable_encoder(DomTreeModel(dom_tree=dom_tree))
    standard_dom_tree = StandardDomTree.from_domtree_dict(dom_tree_json, file_info = file_info)
    json_compatible_data = jsonable_encoder(standard_dom_tree)
    print(json.dumps(json_compatible_data, ensure_ascii=False))

    # 加载test/standard_domtree预期的JSON结果文件test/standard_domtree/result/英文论文Demo_前3页.json 比较 json.dumps(json_compatible_data, ensure_ascii=False)结果是否一致
    result_correct_json = ""
    result_file_path = os.path.join(TEST_PATH, "standard_domtree", "result", "英文论文Demo_前3页.json")
    with open(result_file_path, "r", encoding="utf-8") as f:
        result_correct_json = f.read()

    # 比较生成的结果与预期结果是否一致
    current_result = json.dumps(json_compatible_data, ensure_ascii=False)
    # 将两个JSON字符串解析为Python对象进行比较，避免格式差异导致的误判
    assert json.loads(current_result) == json.loads(result_correct_json), "生成的DOM树与预期结果不一致"
    print("测试通过：生成的DOM树与预期结果一致")


