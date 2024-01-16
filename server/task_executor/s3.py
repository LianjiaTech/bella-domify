import uuid

import boto3
import requests
from fastapi import UploadFile
from settings.ini_config import config

ak = config.get('S3', 'AK')
sk = config.get('S3', 'SK')
bucket_name = config.get('S3', 'BUCKET_NAME')
endpoint = config.get('S3', 'ENDPOINT')
s3 = boto3.client("s3", aws_access_key_id=ak, aws_secret_access_key=sk, endpoint_url=endpoint)


def upload_file(file: UploadFile) -> str:
    # s3 上传文件
    content = file.file.read()
    filename = file.filename
    # gen uuid for file-key
    file_key = uuid.uuid4().hex + filename

    # 上传文件至s3
    s3.put_object(Bucket=bucket_name,
                  Body=content,
                  Key=file_key)
    return file_key


def upload_text_content(text: str) -> str:
    # text to bytes
    file_key = uuid.uuid4().hex + ".txt"
    s3.put_object(Bucket=bucket_name,
                  Body=text.encode("utf-8"),
                  Key=file_key)
    return file_key


def get_file_url(file_key):
    # s3, 获取文件加签url
    return s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': file_key},
                                     ExpiresIn=3600)


def get_file(file_key) -> bytes:
    # 根据file_key获取文件内容
    body = s3.get_object(Bucket=bucket_name, Key=file_key)['Body'].read()
    return body


def get_file_text_content(file_key) -> str:
    return get_file(file_key).decode('utf-8')


if __name__ == "__main__":
    print(get_file_text_content('4d646f6a6b134f8eaf3f800edbc24f2a.txt'))
