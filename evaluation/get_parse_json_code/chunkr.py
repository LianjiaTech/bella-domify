import os
import time

import requests
import json

from evaluation import EVALUATION_WORK_DIR
from evaluation.context import EvaluationConfig

test_dir = os.path.join(EVALUATION_WORK_DIR,'documents')
output_dir =  os.path.join(EVALUATION_WORK_DIR,'parse_json', 'chunkr')

# 评测集文件名
file_list = [
    "中文论文Demo中文文本自动校对综述_4页",
    "自制_4页",
    "英文论文Demo_前3页",
    "评测文件9-博学_13页",
]


def upload_task(file_all_name, api_key):
    files = {
        'file': open(file_all_name, 'rb')
    }
    data = {
        'model': 'HighQuality',
        'target_chunk_length': '512',
        'ocr_strategy': 'Auto'
    }
    headers = {
        'Authorization': f'{api_key}'
    }
    url = "https://api.chunkr.ai/api/v1/task"

    response = requests.post(url, headers=headers, files=files, data=data)

    result = json.loads(response.text)

    task_id = result["task_id"]
    return task_id


def get_result(task_id, api_key):

    url = f"https://api.chunkr.ai/api/v1/task/{task_id}"

    headers = {
        'Authorization': f'{api_key}'
    }

    response = requests.get(url, headers=headers)
    result = json.loads(response.text)

    return result


def get_single_file_parse(file_name, api_key):

    file_all_name = f"{test_dir}/{file_name}.pdf"

    task_id = upload_task(file_all_name, api_key)
    print(file_name)
    print(task_id)

    while True:
        result = get_result(task_id, api_key)
        if result["status"] in ["Succeeded"]:
            data = result["output"]
            json_elements = json.dumps(data, ensure_ascii=False, indent=2)

            with open(f"{output_dir}{file_name}.json", "w") as file:
                file.write(json_elements)

            break
        else:
            print(result["status"])
            time.sleep(5)


if __name__ == "__main__":

    config = EvaluationConfig.from_ini()

    # 从配置中获取Paoding的配置
    if not config.chunkrConfig:
        print("未找到Chunkr配置，请检查配置文件")
        exit(1)

    time0 = time.time()
    for file_name in file_list:
        print(file_name)
        get_single_file_parse(file_name,config.chunkrConfig.api_key)

    time_cost = time.time() - time0
    print(f"运行时间: {int(time_cost // 60)} 分 {(time_cost % 60):.2f} 秒")

