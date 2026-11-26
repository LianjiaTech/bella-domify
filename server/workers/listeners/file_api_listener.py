from server.workers.handlers.file_api_task import file_api_task_callback
from server.workers.handlers.docx2pdf_task import docx2pdf_task_callback
from server.workers.listeners.base import BaseListener
from services.constants import GROUP_ID_LONG_TASK, GROUP_ID_SHORT_TASK, GROUP_ID_IMAGE_TASK, GROUP_ID_DOC_TASK
from settings.ini_config import config

MAX_POLL_INTERVAL_MS = 20 * 60 * 1000


file_api_long_task_config = {
    "bootstrap_servers": config.get('KAFKA', 'file_api_servers', fallback=None),
    "group_id": GROUP_ID_LONG_TASK, # 大文件任务
    "topic": config.get('KAFKA', 'file_api_topic', fallback=None),
    "callback": file_api_task_callback,
    'max.poll.interval.ms': MAX_POLL_INTERVAL_MS,
}
class FileApiLongTaskListener(BaseListener):
    def __init__(self, instance_num):
        super().__init__(instance_num, **file_api_long_task_config)
    
    @classmethod
    def _get_base_config(cls):
        return file_api_long_task_config




file_api_short_task_config = {
    "bootstrap_servers": config.get('KAFKA', 'file_api_servers', fallback=None),
    "group_id": GROUP_ID_SHORT_TASK, # 小文件任务
    "topic": config.get('KAFKA', 'file_api_topic', fallback=None),
    "callback": file_api_task_callback,
    'max.poll.interval.ms': MAX_POLL_INTERVAL_MS,
}
class FileApiShortTaskListener(BaseListener):
    def __init__(self, instance_num):
        super().__init__(instance_num, **file_api_short_task_config)
    
    @classmethod
    def _get_base_config(cls):
        return file_api_short_task_config




file_api_image_task_config = {
    "bootstrap_servers": config.get('KAFKA', 'file_api_servers', fallback=None),
    "group_id": GROUP_ID_IMAGE_TASK, # 图片任务
    "topic": config.get('KAFKA', 'file_api_topic', fallback=None),
    "callback": file_api_task_callback,
    'max.poll.interval.ms': MAX_POLL_INTERVAL_MS,
}
class FileApiImageTaskListener(BaseListener):
    def __init__(self, instance_num):
        super().__init__(instance_num, **file_api_image_task_config)
    
    @classmethod
    def _get_base_config(cls):
        return file_api_image_task_config




file_api_docx2pdf_task_config = {
    "bootstrap_servers": config.get('KAFKA', 'file_api_servers', fallback=None),
    "group_id": GROUP_ID_DOC_TASK, # DOCX转PDF任务
    "topic": config.get('KAFKA', 'file_api_topic', fallback=None),
    "callback": docx2pdf_task_callback,  # 使用专门的 docx2pdf callback
    'max.poll.interval.ms': MAX_POLL_INTERVAL_MS,
}
class FileApiDocx2PdfTaskListener(BaseListener):
    def __init__(self, instance_num):
        super().__init__(instance_num, **file_api_docx2pdf_task_config)
    
    @classmethod
    def _get_base_config(cls):
        return file_api_docx2pdf_task_config