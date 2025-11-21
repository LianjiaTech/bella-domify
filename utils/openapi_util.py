# -*- coding: utf-8 -*-
import json
import requests
from doc_parser.context import logger_context
from services.constants import OPENAI_API_KEY, OPENAPI_HOST

logger = logger_context.get_logger()


def get_ak_code_info(ak_code: str):
    """
    根据 ak_code 获取相关信息
    """
    try:
        url = f"{OPENAPI_HOST}/console/apikey/fetchByCode?code={ak_code}"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return json.loads(response.content)
    except Exception as e:
        logger.error(f"获取ak_code信息失败: {ak_code}, 错误: {e}")
        return None


def get_parent_akcode(ak_code: str):
    """
    获取 parentCode 字段的值
    """
    ak_info = get_ak_code_info(ak_code)
    if ak_info and isinstance(ak_info, dict) and ak_info.get("code") == 200:
        data = ak_info.get("data")
        if data and isinstance(data, dict):
            return data.get("parentCode")
    return None


def fetch_ak_sha_by_code(ak_code: str) -> str:
    """
    根据 akcode 获取 akSha
    
    Returns:
        str: akSha值，如果获取失败则返回空字符串
    """
    if not ak_code:
        return ""
        
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    url = f'{OPENAPI_HOST}/console/apikey/fetchByCode'
    params = {'code': ak_code}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('code') == 200 and 'data' in data:
            ak_sha = data['data'].get('akSha')
            return ak_sha if ak_sha else ""
        else:
            logger.error("fetch ak sha failed : {}".format(ak_code))
            return ""
    except Exception as e:
        logger.error(f"获取ak_sha失败: {ak_code}, 错误: {e}")
        return ""


def report_usage_log(
    user: str,
    model: str,
    usage: dict,
    ak_code: str = None,
    ak_sha: str = None,
    bella_trace_id: str = None,
    endpoint: str = "/v1/chat/completions"
) -> bool:
    """
    上报模型使用到 OpenAPI
    
    Args:
        user: 用户ID
        model: 模型名称
        usage: token 使用信息，包含 completion_tokens, prompt_tokens, total_tokens 等
        ak_code: API Key Code（如果未提供 ak_sha 则必须提供此参数）
        ak_sha: API Key SHA（可选）
        bella_trace_id: Trace ID（可选）
        endpoint: API endpoint，默认为 /v1/chat/completions
    """
    try:
        # 构建请求数据
        log_data = {
            "user": user,
            "model": model,
            "endpoint": endpoint,
            "usage": usage
        }

        # 添加可选字段
        if ak_sha:
            log_data["akSha"] = ak_sha
        if ak_code:
            log_data["akCode"] = ak_code
        if bella_trace_id:
            log_data["bellaTraceId"] = bella_trace_id
        # 发送请求
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        url = f'{OPENAPI_HOST}/v1/log'
        response = requests.post(url, headers=headers, json=log_data, timeout=5)
        response.raise_for_status()

        logger.info(f"Usage log reported successfully for user={user}, model={model}, total_tokens={usage.get('total_tokens', 0)}")
        return True
    except Exception as e:
        logger.error(f"Unexpected error when reporting usage log: {str(e)}")
        return False

