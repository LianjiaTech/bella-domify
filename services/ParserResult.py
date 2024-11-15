# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/11/15
#    @Description   : 
#
# ===============================================================
from enum import Enum


class ParserCode(Enum):
    SUCCESS = "success"
    ERROR = "error"


class ParserMsg(Enum):
    SUCCESS = "解析成功"


class ParserResult:
    def __init__(self, parser_code=ParserCode.SUCCESS, parser_msg=ParserCode.SUCCESS, parser_data=None):
        self.parser_code = parser_code
        self.parser_data = parser_data
        self.parser_msg = parser_msg

    def to_json(self):
        return {
            "parser_code": self.parser_code,
            "parser_msg": self.parser_msg,
            "parser_data": self.parser_data,
        }
