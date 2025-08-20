from functools import cache
from typing import List

from bella_openapi.console import get_model_list

from doc_parser.dom_parser.provider.vision_model_provider import VisionModelProvider


class OpenAIVisionModelProvider(VisionModelProvider):

    @cache
    def get_model_list(self) -> List[str]:
        """
        获取OpenAI Vision模型列表

        Returns:
            List[str]: OpenAI Vision模型列表
        """
        models = get_model_list(extra_query={"status": "active", "features": "vision"})
        return [model['modelName'] for model in models.get('data', [])]
