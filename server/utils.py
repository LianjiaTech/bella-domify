# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/7/16
#    @Description   : 
#
# ===============================================================
import time
import random
from server.constants import IMAGE
from server import s3_service
from io import BytesIO


def get_random_name():
    timestamp = str(int(time.time()))
    return timestamp + ''.join(random.choices('0123456789', k=6))


def build_image_item(image_blob, bbox=(0, 0)):
    filename = IMAGE + get_random_name()
    image_s3_url = s3_service.s3_upload(filename=filename, data=BytesIO(image_blob))
    if bbox == (0, 0):
        return dict(text=image_s3_url, type=IMAGE)
    else:
        return dict(text=image_s3_url, type=IMAGE, bbox=bbox)
