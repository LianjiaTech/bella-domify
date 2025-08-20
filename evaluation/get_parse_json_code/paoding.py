import hashlib
import os
import urllib.parse
from datetime import datetime
import requests
import json

from evaluation import EVALUATION_WORK_DIR
from evaluation.context import EvaluationConfig

test_dir = os.path.join(EVALUATION_WORK_DIR,'documents')

output_dir =  os.path.join(EVALUATION_WORK_DIR,'parse_json', 'paoding')

# 评测集文件名
file_list = [
    "中文论文Demo中文文本自动校对综述_4页",
    "自制_4页",
    "英文论文Demo_前3页",
    "评测文件9-博学_13页",
]


def revise_url(url, extra_params=None, excludes=None):
    extra_params = extra_params or {}
    excludes = excludes or []
    # main_url, query = urllib.parse.splitquery(url)
    parsed_url = urllib.parse.urlparse(url)
    main_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
    query = parsed_url.query

    params = urllib.parse.parse_qs(query) if query else {}
    params.update(extra_params)
    keys = list(params.keys())
    keys.sort()
    params_strings = []
    for key in keys:
        if key in excludes:
            continue
        values = params[key]
        if isinstance(values, list):
            values.sort()
            params_strings.extend(["{}={}".format(key, urllib.parse.quote(str(value))) for value in values])
        else:
            params_strings.append("{}={}".format(key, urllib.parse.quote(str(values))))

    return "{}?{}".format(main_url, "&".join(params_strings)) if params_strings else main_url


def generate_timestamp():
    delta = datetime.utcnow() - datetime.utcfromtimestamp(0)
    return int(delta.total_seconds())


def _generate_token(url, app_id, secret_key, extra_params=None, timestamp=None):
    url = revise_url(url, extra_params=extra_params, excludes=["_token", "_timestamp"])
    timestamp_now = timestamp or generate_timestamp()
    source = "{}#{}#{}#{}".format(url, app_id, secret_key, timestamp_now)
    token = hashlib.md5(source.encode()).hexdigest()
    return token


def encode_url(url, app_id, secret_key, params=None, timestamp=None):
    timestamp = timestamp or generate_timestamp()
    token = _generate_token(url, app_id, secret_key, params, timestamp)
    extra_params = {
        '_timestamp': timestamp,
        '_token': token
    }
    extra_params.update(params or {})
    url = revise_url(url, extra_params=extra_params)
    return url



def get_single_file_parse(file_name, app_id, user, token):

    file_all_name = f"{test_dir}/{file_name}.pdf"

    uuid = upload_task(file_all_name, app_id, user, token)
    print(file_name)
    print(uuid)

    URL = f"https://saas.pdflux.com/api/v1/saas/document/{uuid}/pdftables?user={user}"  # 获取解析结果

    url = encode_url(URL, app_id, token)
    print(url)
    # 这里打好断点，用网页能访问之后，再让程序继续

    response = requests.get(url)
    print(response.text[:1000])

    data = response.json()
    # 将结果写入到一个JSON文件中
    with open(f"{output_dir}/{file_name}.json", 'w') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)


def upload_task(file_all_name, app_id, user, token):
    url = get_token(app_id, user, token)
    print("upload_task url:" + url)
        # 打开文件并发送POST请求
    with open(file_all_name, 'rb') as file:
        files = {'file': file}
        response = requests.post(url, files=files)
    # 打印响应内容
    print(response.text)
    result = json.loads(response.text)
    uuid = result["data"]["uuid"]
    return uuid


def get_token(app_id, user, token):
    URL = f"https://saas.pdflux.com/api/v1/saas/upload?user={user}&force_update=true"  # 获取Token
    url = encode_url(URL, app_id, token)
    return url


if __name__ == '__main__':
    config = EvaluationConfig.from_ini()

    # 从配置中获取Paoding的配置
    if not config.paodingConfig:
        print("未找到Paoding配置，请检查配置文件")
        exit(1)

    for file_name in file_list:
        print(file_name)
        get_single_file_parse(file_name, config.paodingConfig.app_id, config.paodingConfig.user, config.paodingConfig.secret_key)


