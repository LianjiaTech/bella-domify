import hashlib
import io
import json
import time
import urllib.parse
import uuid
from urllib.parse import urlparse, urlunparse

import boto3
from fastapi import UploadFile

from doc_parser.context import logger_context
from settings.ini_config import config

logger = logger_context.get_logger()

ak = config.get('S3', 'AK')
sk = config.get('S3', 'SK')
bucket_name = config.get('S3', 'BUCKET_NAME')
endpoint = config.get('S3', 'ENDPOINT')
out_endpoint = config.get('S3', 'OUT_ENDPOINT')
s3 = boto3.client("s3", aws_access_key_id=ak, aws_secret_access_key=sk, endpoint_url=endpoint)

def upload_file(file: UploadFile = None, stream: bytes = None, filename="") -> str:
    # s3 上传文件
    if file:
        content = file.file.read()
        stream = io.BytesIO(content)
        filename = file.filename

    # gen uuid for file-key
    file_key = uuid.uuid4().hex + filename

    # 上传文件至s3
    s3.put_object(Bucket=bucket_name,
                  Body=stream,
                  Key=file_key)
    return file_key


def upload_dict_content(data: dict, file_key: str) -> str:
    json_data = json.dumps(data)
    s3.put_object(Bucket=bucket_name,
                  Body=json_data,
                  Key=file_key)
    return file_key


def get_file_url_inner(file_key):
    # s3, 获取文件加签url
    return s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': file_key},
                                     ExpiresIn=10 * 365 * 24 * 60* 60)  # 10年有效期


def get_file(file_key) -> bytes:
    # 根据file_key获取文件内容
    body = s3.get_object(Bucket=bucket_name, Key=file_key)['Body'].read()
    return body


def get_file_text_content(file_key) -> str:
    return get_file(file_key).decode('utf-8')


def replace_inner_to_outer_url(url: str) -> str:
    if not url:
        return url

    if url.startswith("http:"):
        url = url.replace("http:", "https:")

    # 替换内网地址为外网地址
    return url.replace(endpoint, out_endpoint)


def get_sign_url_with_given_end_time(url, start_time: int, expire_seconds: int) -> str:
    uri = urlparse(replace_inner_to_outer_url(url))
    host = uri.netloc
    path = uri.path
    try:
        decode_path = urllib.parse.unquote(path)
    except Exception as e:
        logger.error(e)
        decode_path = path

    expire_time = start_time + expire_seconds

    sign_builder = f"ak={ak}&exp={expire_time}&path={decode_path}&ts={start_time}&sk={sk}"
    sign = hashlib.md5(sign_builder.encode('utf-8')).hexdigest()

    params = f"ak={ak}&exp={expire_time}&ts={start_time}&sign={sign}"

    signed_url = urlunparse((uri.scheme, host, path, '', params, ''))
    return signed_url


def get_file_url(file_key):
    url_inner = get_file_url_inner(file_key)
    url_outer = get_sign_url_with_given_end_time(url_inner, int(time.time()), 10 * 365 * 24 * 60* 60)  # 10年有效期
    return url_outer