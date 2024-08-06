# -*- coding: utf-8 -*-
# ======================
# Date    : 8/6/24
# Author  : Liu Yuchen
# Content : 
# 
# ======================
import contextvars


user_context = contextvars.ContextVar("user_context")

# TODO 兼容阶段，业务方添加 user 之后下掉
DEFAULT_USER = "1000000020353701"
