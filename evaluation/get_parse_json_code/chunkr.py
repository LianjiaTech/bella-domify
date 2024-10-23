import time

import requests
import json

url = "https://api.chunkr.ai/api/v1/task"
api_key = "lu_dYPtC3iKCeV_AKi8F9DHokyyXea9u7m1V7tdcmAFG499V"  # 请替换为你的API密钥

test_dir = '/Users/lucio/code/document_parse/evaluation/documents/'

output_dir = '/Users/lucio/code/document_parse/evaluation/parse_json/chunkr/'

# 评测集文件名
file_list = [
    # "评测文件1-喵回QA_3页",
    "《贝壳入职管理制度》5页",
    "《贝壳离职管理制度V3.0》5页",
    "中文论文Demo中文文本自动校对综述_4页",
    "自制_4页",
    "花桥学院业务核算指引_6页",
    "英文论文Demo_前3页",
    "评测文件9-博学_13页",
]

file_name = "《贝壳入职管理制度》5页"
# file_name = "《贝壳离职管理制度V3.0》5页"
# file_name = "花桥学院业务核算指引_6页"
# file_name = "英文论文Demo_前3页"
# file_name = "中文论文Demo中文文本自动校对综述_4页"
# file_name = "自制_4页"
# file_name = "评测文件9-博学_13页"




def upload_task(file_all_name):
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
    response = requests.post(url, headers=headers, files=files, data=data)

    result = json.loads(response.text)

    task_id = result["task_id"]
    return task_id


def get_result(task_id):

    url = f"https://api.chunkr.ai/api/v1/task/{task_id}"

    headers = {
        'Authorization': f'{api_key}'
    }

    response = requests.get(url, headers=headers)
    result = json.loads(response.text)

    return result


def get_single_file_parse(file_name):

    file_all_name = f"{test_dir}{file_name}.pdf"


    task_id = upload_task(file_all_name)
    print(file_name)
    print(task_id)


    while True:
        result = get_result(task_id)
        if result["status"] != "Starting":
            data = result["output"]
            json_elements = json.dumps(data, ensure_ascii=False, indent=2)

            with open(f"{output_dir}{file_name}.json", "w") as file:
                file.write(json_elements)

            break
        else:
            print(result["status"])
            time.sleep(5)


if __name__ == "__main__":
    time0 = time.time()
    get_single_file_parse(file_name)
    # for file_name in file_list:
    #     get_single_file_parse(file_name)

    time_cost = time.time() - time0
    print(f"运行时间: {int(time_cost // 60)} 分 {(time_cost % 60):.2f} 秒")

