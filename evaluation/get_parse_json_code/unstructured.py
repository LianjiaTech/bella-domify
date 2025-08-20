# ===========================
#
# https://docs.unstructured.io/api-reference/api-services/sdk-python
# ===========================
import json
import os

import unstructured_client
from unstructured_client.models import operations, shared

from evaluation import EVALUATION_WORK_DIR
from evaluation.context import EvaluationConfig

test_dir = os.path.join(EVALUATION_WORK_DIR,'documents')

output_dir =  os.path.join(EVALUATION_WORK_DIR,'parse_json', 'unstructured')

if __name__ == '__main__':
    config = EvaluationConfig.from_ini()
    # 评测集文件名
    file_list = [
        "中文论文Demo中文文本自动校对综述_4页",
        "自制_4页",
        "英文论文Demo_前3页",
        "评测文件9-博学_13页",
    ]

    # 从配置中获取Paoding的配置
    if not config.unstructuredConfig:
        print("未找到Unstructured配置，请检查配置文件")
        exit(1)


    client = unstructured_client.UnstructuredClient(
        api_key_auth=config.unstructuredConfig.api_key,
        server_url=config.unstructuredConfig.server_url,
    )

    for file_name in file_list:
        filename = f"{test_dir}/{file_name}.pdf"

        print(file_name)

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

            with open(f"{output_dir}/{file_name}.json", "w") as file:
                file.write(json_elements)
        except Exception as e:
            print(e)