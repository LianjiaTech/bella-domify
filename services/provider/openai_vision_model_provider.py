from functools import cache
from typing import List

import httpx
from bella_openapi.config import openapi_config

from doc_parser.dom_parser.provider.vision_model_provider import VisionModelProvider
from services.constants import HTTP_TIMEOUT_SECONDS


class OpenAIVisionModelProvider(VisionModelProvider):

    @cache
    def get_model_list(self) -> List[str]:
        """
        获取OpenAI Vision模型列表

        Returns:
            List[str]: OpenAI Vision模型列表
        """
        response = httpx.get(
            openapi_config.OPENAPI_HOST + '/console/model/list',
            headers={'Authorization': openapi_config.OPENAPI_CONSOLE_KEY, 'Content-Type': 'application/json'},
            params={'status': 'active', 'features': 'vision'},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return [model['modelName'] for model in response.json().get('data', [])]
