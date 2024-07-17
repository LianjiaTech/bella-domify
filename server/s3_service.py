import hashlib
import time

import boto3

# public_s3 = {
#     "ACCESS_KEY": s3_settings.ACCESS_KEY,
#     "SECERT_ACCESS_KEY": s3_settings.SECERT_ACCESS_KEY,
#     "REGION_NAME": s3_settings.REGION_NAME,
#     "BUCKET_NAME": s3_settings.BUCKET_NAME,
#     "ENDPOINT_URL": s3_settings.ENDPOINT_URL,
#     # "DOMAIN": "https://img.ljcdn.com"
#     "DOMAIN": s3_settings.DOMAIN
# }

# openapi-assistant
public_s3 = {
    "ACCESS_KEY": "QACGA0JKK1D24X92E67C",
    "SECERT_ACCESS_KEY": "SChMFsXKA9fcllrJnsscYmVtwCmR1GguUBRZuuBD",
    "REGION_NAME": "cn-north-1",
    "BUCKET_NAME": "openapi-assistant",
    "ENDPOINT_URL": "http://storage.lianjia.com",
    # "DOMAIN": "https://img.ljcdn.com"
    "DOMAIN": "https://img.ljcdn.com"
}


class S3(object):

    def __init__(self):
        self.access_key = public_s3["ACCESS_KEY"]
        self.secret_access_key = public_s3["SECERT_ACCESS_KEY"]
        self.region_name = public_s3["REGION_NAME"]
        self.bucket_name = public_s3["BUCKET_NAME"]
        self.endpoint_url = public_s3["ENDPOINT_URL"]
        self.domain = public_s3["DOMAIN"]
        try:
            self.session = boto3.session.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region_name
            )
            self.s3 = self.session.resource('s3', region_name=self.region_name, endpoint_url=self.endpoint_url)
            self.bucket = self.s3.Bucket(self.bucket_name)
        except Exception as e:
            print('s3 connect error. msg:%s' % (repr(e)))

    def upload_file(self, filename, data, is_sign):
        if self.bucket is None:
            return False
        try:
            self.bucket.put_object(Key=filename, Body=data)
            if is_sign:
                return self.get_url_sign(filename)
            else:
                return self.get_url(filename)
        except Exception as e:
            print('s3 upload file failure. msg:%s' % (repr(e)))
            return False

    def get_url_sign(self, filename):
        if filename is None:
            return False
        domain = self.domain  # 'https://img.ljcdn.com'
        # expire = 1800000
        path = '/%s/%s' % (self.bucket_name, filename)
        ak = self.access_key
        sk = self.secret_access_key
        ts = int(time.time())

        # data = [('ak', ak), ('path', path), ('ts', ts), ('exp', expire)]
        data = [('ak', ak), ('path', path), ('ts', ts)]
        data = sorted(data)

        verify = ''
        for (key, value) in data:
            verify = "%s%s=%s&" % (verify, key.strip(), value)
        verify = "%ssk=%s" % (verify, sk)
        sign = hashlib.md5(verify.encode('utf-8')).hexdigest()
        return '%s%s?ak=%s&ts=%s&sign=%s' % (domain, path, ak, ts, sign)
        # return '%s%s?ak=%s&exp=%s&ts=%s&sign=%s' % (domain, path, ak, expire, ts, sign)

    def get_url(self, filename):
        if filename is None:
            return False
        domain = self.domain  # 'https://img.ljcdn.com'
        path = '/%s/%s' % (self.bucket_name, filename)
        return '%s%s' % (domain, path)


def s3_upload(filename, data):
    s3 = S3()
    s3.upload_file(data=data, filename=filename, is_sign=True)
    response = s3.get_url(filename=filename)
    return response


if __name__ == "__main__":

    file_name = '/Users/lucio/code/others/工作内容/工作内容2024/0709多文件类型解析代码调研/demo.pptx'

    # 读取本地文件
    try:
        with open(file_name, 'rb') as file:
            buf_data = file.read()
    except Exception as e:
        print(f"读取文件失败: {e}")

    response = s3_upload(filename=file_name, data=buf_data)
    print(response)
