# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/7/30
#    @Description   : 
#
# ===============================================================
from services.constants import IMAGE
from utils.general_util import get_pic_url_and_ocr


class SimpleBlock:
    def __init__(self, text="", type="", page_num=0, is_header=False, is_footer=False, image_bytes=None, ocr_text=""):
        self.text = text
        self.ocr_text = ocr_text
        self.type = type  # 枚举值：IMAGE, TEXT, TABLE
        self.page_num = page_num
        self.is_header = is_header
        self.is_footer = is_footer
        self.image_bytes = image_bytes

    def get_result(self):
        return {
            "text": self.text,
            "ocr_result": self.ocr_text,
            "type": self.type,
            "page_num": self.page_num,
        }

    def generate_s3_url(self, user):
        if self.type == IMAGE and self.image_bytes:
            image_s3_url, ocr_text = get_pic_url_and_ocr(self.image_bytes, user)
            self.text = image_s3_url
            self.ocr_text = ocr_text
        return True

    def mark_holder(self, header: bool = True):
        if header:
            self.is_header = True
        else:
            self.is_footer = True
