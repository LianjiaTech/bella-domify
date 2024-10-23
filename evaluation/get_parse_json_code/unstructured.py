# ===========================
#
# https://docs.unstructured.io/api-reference/api-services/sdk-python
# ===========================
import json

import unstructured_client
from unstructured_client.models import operations, shared


UNSTRUCTURED_API_KEY = "iIwEB1rLIV0DpJvK1PEqGSXAbvXKuU"
UNSTRUCTURED_API_URL = "https://api.unstructured.io/general/v0/general"

test_dir = '/Users/lucio/code/document_parse/evaluation/documents/'

output_dir = '/Users/lucio/code/document_parse/evaluation/parse_json/unstructured/'

# file_name = "评测文件1-喵回QA_3页"
# file_name = "《贝壳入职管理制度》5页"
# file_name = "《贝壳离职管理制度V3.0》5页"
# file_name = "花桥学院业务核算指引_6页"
# file_name = "英文论文Demo_前3页"
# file_name = "中文论文Demo中文文本自动校对综述_4页"
# file_name = "自制_4页"
file_name = "评测文件9-博学_13页"


# test_dir = "../test_document/"


client = unstructured_client.UnstructuredClient(
    api_key_auth=UNSTRUCTURED_API_KEY,
    server_url=UNSTRUCTURED_API_URL,
)

filename = f"{test_dir}{file_name}.pdf"

req = operations.PartitionRequest(
    partition_parameters=shared.PartitionParameters(
        files=shared.Files(
            content=open(filename, "rb"),
            file_name=filename,
        ),
        strategy=shared.Strategy.HI_RES,
        coordinates=True,  # 要不要bbox
        languages=["chi_sim", "eng"],   # https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html
        split_pdf_page=True,  # If True, splits the PDF file into smaller chunks of pages.
        split_pdf_allow_failed=True,  # If True, the partitioning continues even if some pages fail.
        split_pdf_concurrency_level=15,  # Set the number of concurrent request to the maximum value: 15.
        # extract_image_block_types=["Image", "Table"],  # 是否需要base64
        starting_page_number=True,  # 页码，是从1开始的
    ),
)

try:
    res = client.general.partition(request=req)
    element_dicts = [element for element in res.elements]

    # Print the processed data's first element only.
    print(element_dicts[0])

    # Write the processed data to a local file.
    json_elements = json.dumps(element_dicts, ensure_ascii=False, indent=2)

    with open(f"{output_dir}{file_name}.json", "w") as file:
        file.write(json_elements)
except Exception as e:
    print(e)


if __name__ == "__main__":
    pass