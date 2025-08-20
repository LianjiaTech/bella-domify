# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu
#    @Create Time   : 2024/12/20
#    @Description   : 
#
# ===============================================================
import os

import requests
import mimetypes
import time

from evaluation import EVALUATION_WORK_DIR
from evaluation.context import EvaluationConfig

test_dir = os.path.join(EVALUATION_WORK_DIR,'documents')
output_dir =  os.path.join(EVALUATION_WORK_DIR,'parse_json', 'llamaparse')

def get_result(file_name, api_key, need_save=True):

    headers = {"Authorization": f"Bearer {api_key}"}
    file_path = f"{test_dir}/{file_name}.pdf"
    base_url = "https://api.cloud.llamaindex.ai/api/parsing"

    with open(file_path, "rb") as f:
        mime_type = mimetypes.guess_type(file_path)[0]
        files = {"file": (f.name, f, mime_type)}
        # data = {
        #     # 'auto_mode': 'true',
        #     'continuous_mode': 'true',
        #     # 'premium_mode': 'true',
        #
        # }
        data = {
            # 'auto_mode': True,
            # 'fast_mode': True,
            'continuous_mode': False,
            'premium_mode': True,
            'input_url': '',
            'structured_output': False,
            'disable_ocr': False,
            'disable_image_extraction': False,
            'annotate_links': False,
            'do_not_unroll_columns': False,
            'html_make_all_elements_visible': False,
            'html_remove_navigation_elements': False,
            'html_remove_fixed_elements': False,
            'guess_xlsx_sheet_name': False,
            'do_not_cache': False,
            'invalidate_cache': False,
            'output_pdf_of_document': False,
            'take_screenshot': False
        }
        print(data)

        # send the request, upload the file
        url = f"{base_url}/upload"
        # response = requests.post(url, headers=headers, files=files)
        response = requests.post(url, headers=headers, files=files, data=data)

    response.raise_for_status()
    # get the job id for the result_url
    job_id = response.json()["id"]
    # result_type = "text"  # or "markdown"
    result_type = "markdown"  # or "markdown"
    # result_type = "json"  # or "markdown"
    result_url = f"{base_url}/job/{job_id}/result/{result_type}"

    # check for the result until its ready
    while True:
        try:
            response = requests.get(result_url, headers=headers)
            print(response.status_code)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")

        time.sleep(2)

    # download the result
    result = response.json()
    output = result[result_type]

    print(output)
    if need_save:
        with open(f"{output_dir}/{file_name}.pdf.md", "w", encoding="utf-8") as file:
            file.write(output)
    return output


def get_result_list(api_key):
    file_list = [
        "中文论文Demo中文文本自动校对综述_4页",
        "自制_4页",
        "英文论文Demo_前3页",
        "评测文件9-博学_13页",
    ]

    for file_name in file_list:
        print(file_name)
        get_result(file_name, api_key)
        time.sleep(5)


if __name__ == "__main__":
    config = EvaluationConfig.from_ini()

    # 从配置中获取Paoding的配置
    if not config.llamaparseConfig:
        print("未找到Llamaparse配置，请检查配置文件")
        exit(1)

    get_result_list(config.llamaparseConfig.api_key)
