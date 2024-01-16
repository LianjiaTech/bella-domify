import uuid
from threading import Thread

from fastapi import UploadFile
import boto3

from .db.model import create_task as create_task_in_db
from .db.model import get_wait_task

ak = 'Q265N5ELG32TT7UWO8YJ'
sk = 'fcFeEgba8PY5kUMFfznnGwmA8390hhKa8rckLWJD'
bucket_name = 'cv-aigc'
endpoint = 'https://storage.lianjia.com'
s3 = boto3.client("s3", aws_access_key_id=ak, aws_secret_access_key=sk, endpoint_url=endpoint)


def upload_pdf_file(file: UploadFile) -> str:
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


def create_pdf_parse_task(file: UploadFile, callback_url) -> str:
    file_key = upload_pdf_file(file)
    task_id = uuid.uuid4().hex
    create_task_in_db(task_id=task_id, file_key=file_key, file_type='pdf', callback_url = callback_url)
    return task_id


def get_pdf_parse_task():
    return get_wait_task()


def get_file_url(file_key):
    # s3, 获取文件加签url
    return s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': file_key},
                                     ExpiresIn=3600)
