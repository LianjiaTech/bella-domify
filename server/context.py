# -*- coding: utf-8 -*-
# ======================
# Date    : 8/6/24
# Author  : Liu Yuchen
# Content : 
# 
# ======================
import contextvars


user_context = contextvars.ContextVar("user_context")

# review-TODO 配置化
DEFAULT_USER = "1000000020353701"
