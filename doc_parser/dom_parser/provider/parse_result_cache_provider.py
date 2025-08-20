from abc import ABC, abstractmethod


class ParseResultCacheProvider(ABC):

    # 解析结果获取
    def get_parse_result(self, task_id, parse_type=""):
        raise NotImplementedError("子类必须实现 get_parse_result 方法")

    # 解析结果上传
    @abstractmethod
    def upload_parse_result(self, task_id, parse_result, parse_type):
        raise NotImplementedError("子类必须实现 upload_parse_result 方法")
