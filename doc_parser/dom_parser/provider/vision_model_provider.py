from abc import ABC, abstractmethod
from typing import List


# 定义 Provider 接口
class VisionModelProvider(ABC):

    @abstractmethod
    def get_model_list(self) -> List[str]:
        """获取视觉模型列表"""
        raise NotImplementedError("子类必须实现获取视觉模型列表的方法")
