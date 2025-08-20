from server.workers.handlers.file_api_task import file_api_task_callback
from server.workers.listeners.base import BaseListener
from services.constants import GROUP_ID_LONG_TASK, GROUP_ID_SHORT_TASK, GROUP_ID_IMAGE_TASK
from settings.ini_config import config


file_api_long_task_config = {
    "bootstrap_servers": config.get('KAFKA', 'file_api_servers', fallback=None),
    "group_id": GROUP_ID_LONG_TASK, # 大文件任务
    "topic": config.get('KAFKA', 'file_api_topic', fallback=None),
    "callback": file_api_task_callback,
    "callback_timeout": 5 * 60,  # 执行超时时间5min，需要读取文件（秒）
    'max.poll.interval.ms': 10 * 60 *1000,  # 10min,避免_MAX_POLL_EXCEEDED
}
class FileApiLongTaskListener(BaseListener):
    def __init__(self, instance_num):
        super().__init__(instance_num, **file_api_long_task_config)




file_api_short_task_config = {
    "bootstrap_servers": config.get('KAFKA', 'file_api_servers', fallback=None),
    "group_id": GROUP_ID_SHORT_TASK, # 小文件任务
    "topic": config.get('KAFKA', 'file_api_topic', fallback=None),
    "callback": file_api_task_callback,
    "callback_timeout": 5 * 60,  # 执行超时时间5min，需要读取文件（秒）
    'max.poll.interval.ms': 10 * 60 *1000,  # 10min,避免_MAX_POLL_EXCEEDED
}
class FileApiShortTaskListener(BaseListener):
    def __init__(self, instance_num):
        super().__init__(instance_num, **file_api_short_task_config)




file_api_image_task_config = {
    "bootstrap_servers": config.get('KAFKA', 'file_api_servers', fallback=None),
    "group_id": GROUP_ID_IMAGE_TASK, # 图片任务
    "topic": config.get('KAFKA', 'file_api_topic', fallback=None),
    "callback": file_api_task_callback,
    "callback_timeout": 5 * 60,  # 执行超时时间5min，需要读取文件（秒）
    'max.poll.interval.ms': 10 * 60 *1000,  # 10min,避免_MAX_POLL_EXCEEDED
}
class FileApiImageTaskListener(BaseListener):
    def __init__(self, instance_num):
        super().__init__(instance_num, **file_api_image_task_config)