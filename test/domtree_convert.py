import json
import uuid

from fastapi.encoders import jsonable_encoder

from server.protocol.standard_domtree import StandardDomTree
from services.parse_manager import file_api_retrieve_file, file_api_get_file_info, domtree_parse


def test_domtree_convert():
    file_id = "file-2506061426450028000313-273737144"  # 替换为实际的文件ID
    # file_id = "file-2506050858410019035509-1052769292"  # 有表格
    # file_id = "file-2506181733010028000364-273737144"
    # 读取文件流内容
    contents = file_api_retrieve_file(file_id)
    file_info = file_api_get_file_info(file_id)
    file_info = file_api_get_file_info("file-2506191738240030000002-2075695711")

    domtree = domtree_parse(file_info['filename'], contents, file_id)[1]
    json_str = json.dumps(domtree, indent=2, ensure_ascii=False)
    standard_dom_tree = StandardDomTree.from_domtree_dict(domtree, file_info = file_info)
    json_compatible_data = jsonable_encoder(standard_dom_tree)
    print(json.dumps(json_compatible_data, indent=2, ensure_ascii=False))