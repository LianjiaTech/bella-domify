# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/11/5
#    @Description   : 
#
# ===============================================================
import io

from common.tool.webdav3.client import Client

from settings.ini_config import config

CHUBAOFS = {
    "HOSTNAME": config.get('CHUBAOFS', 'hostname'),
    "USERNAME": config.get('CHUBAOFS', 'username'),
    "PASSWORD": config.get('CHUBAOFS', 'password'),
}


class ChuBaoFSTool:

    def __init__(self):
        options = {
            "webdav_hostname": CHUBAOFS["HOSTNAME"],
            "webdav_login": CHUBAOFS["USERNAME"],
            "webdav_password": CHUBAOFS["PASSWORD"],
            "webdav_disable_check": True
        }

        client = Client(options)
        client.webdav.disable_check = False
        # To not check SSL certificates (Default = True)
        client.verify = False
        self.client = client

    def get_client(self):
        return self.client

    def read_file(self, file_path):
        resource = self.client.resource(file_path)
        stream = io.BytesIO()
        resource.write_to(stream)
        stream.seek(0)
        return stream

    def download_file(self, file_path, local_path):
        self.client.download(file_path, local_path)


if __name__ == "__main__":

    chubao = ChuBaoFSTool()
    # file_path = "1000000023008327/app_data/belle/默认/《贝壳离职管理制度V3.0》5页.pdf"
    file_path = "1000000023008327/app_data/belle/默认/《贝壳入职管理制度》5页.pdf"
    stream = chubao.read_file(file_path)
    print()
    # file_type = get_file_type(file_path)