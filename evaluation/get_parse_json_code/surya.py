import time

import requests
import json

url = "https://api.chunkr.ai/api/v1/task"
api_key = "Ald-VVcSBS3Us8R2oC1_DBXiIwTGqeofAQthzowNxJQ"  # 请替换为你的API密钥
headers = {"X-Api-Key": api_key}


test_dir = '/Users/lucio/code/document_parse/evaluation/documents/'

output_dir = '/Users/lucio/code/document_parse/evaluation/parse_json/surya/'

# file_name = "评测文件1-喵回QA_3页"
# file_name = "《贝壳入职管理制度》5页"
# file_name = "《贝壳离职管理制度V3.0》5页"
# file_name = "花桥学院业务核算指引_6页"
# file_name = "英文论文Demo_前3页"
# file_name = "中文论文Demo中文文本自动校对综述_4页"
# file_name = "自制_4页"
file_name = "评测文件9-博学_13页"


filename = f"{test_dir}{file_name}.pdf"


def upload_task(filename):

    url = "https://www.datalab.to/api/v1/layout"

    form_data = {
        'file': ('test.pdf', open(filename, 'rb'), 'application/pdf'),
    }

    response = requests.post(url, files=form_data, headers=headers)
    data = response.json()
    check_url = data["request_check_url"]
    return check_url



def get_single_file_parse(filename):
    check_url = upload_task(filename)

    while True:
        response = requests.get(check_url, headers=headers)  # Don't forget to send the auth headers
        data = response.json()

        if data["status"] == "complete":
            result = data["pages"]
            json_elements = json.dumps(result, ensure_ascii=False, indent=2)

            with open(f"{output_dir}{file_name}.json", "w") as file:
                file.write(json_elements)

            break
        else:
            print(data["status"])
            time.sleep(5)


if __name__ == "__main__":
    time0 = time.time()

    get_single_file_parse(filename)

    time1 = time.time()
    print(f"运行时间: {int((time1) - int(time0) // 60)} 分 {((time1 - time0) % 60):.2f} 秒")