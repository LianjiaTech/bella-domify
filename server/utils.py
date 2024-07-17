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


def get_random_name():
    timestamp = str(int(time.time()))
    return timestamp + ''.join(random.choices('0123456789', k=6))
