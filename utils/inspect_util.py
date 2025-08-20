import inspect
from functools import lru_cache


@lru_cache(maxsize=None)  # 使用 LRU 缓存装饰器
def get_signature(func):
    return inspect.signature(func)


def has_parameter(func, param_name):
    # 使用缓存的签名
    sig = get_signature(func)
    # 检查参数是否在签名中
    return param_name in sig.parameters
