from typing import Dict, Optional


def get_service_client_headers(ak_code: Optional[str]) -> Optional[Dict[str, str]]:
    """系统凭证和编码均非空时组装代理请求头，否则返回 None 使用原鉴权。"""
    from settings.ini_config import config

    token = config.get('OCR', 'service_client_token', fallback='').strip()
    code = config.get('OCR', 'service_client_code', fallback='').strip()
    if not token or not code:
        return None
    if not ak_code:
        raise ValueError("ServiceClient 调用缺少任务 AK Code")

    return {
        "Authorization": f"Bearer {token}",
        "X-Service-Client": code,
        "X-Effective-Api-Key-Code": ak_code,
    }
