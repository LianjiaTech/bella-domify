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
from services.constants import IMAGE
from server.task_executor import s3
from services.SimpleBlock import SimpleBlock


def build_image_item(image_blob):
    file_key = s3.upload_file(stream=image_blob)
    image_s3_url = s3.get_file_url(file_key)
    return SimpleBlock(type=IMAGE, text=image_s3_url)
