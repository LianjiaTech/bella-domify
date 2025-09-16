import json
from services.parse_manager import DOCUMENT_PARSE_FAIL
from doc_parser.context import logger_context, parser_context
from doc_parser.layout_parser import pptx_parser, docx_parser, pdf_parser
from server.common.exception import BusinessError
from server.common.file_validation import check_file_size
from services import parse_manager
from services.constants import GROUP_ID_IMAGE_TASK, GROUP_ID_LONG_TASK, GROUP_ID_SHORT_TASK, GROUP_ID_DOC_TASK
from utils import general_util
from settings.ini_config import config

logger = logger_context.get_logger()

def file_api_task_callback(payload: dict, consumer_info: dict) -> bool:
    """
    file api消息体结构
    {
        "event": "file.created",
        "data": {
            "id": "file-abc123",
            "object": "file",
            "bytes": 175,
            "created_at": 1613677385,
            "filename": "salesOverview.pdf",
            "purpose": "assistants",
            "space_code": "1000000012345678",
            "cuid": 1000000012345678,
            "cu_name": "张三",
        },
        "metadata": {
                "post_processors":["file_indexing"],
                "user": "0000000000000001",
                "callbacks":[]
            }
    }
    业务方数据存储在metadata内部。bella侧定义了几种metadata参数
    """
    logger.info(f'receive event from file api : {json.dumps(payload)}')
    data = payload.get('data')

    # 监听文件创建和更新事件
    event = payload.get('event')
    if not data or event not in ["file.created", "file.updated"]:
        return True

    # 只处理purpose为assistants类型的文件
    if data.get('purpose') != 'assistants':
        logger.info(f"File {data.get('id')} purpose is not 'assistants': {data.get('purpose')}")
        return True

    # 对于file.updated事件，只关注文件内容修改
    if event == "file.updated" and payload.get('scope') != 'content':
        return True

    # 检查metadata是否为dict类型，如果不是则返回True
    metadata = {}
    try:
        if payload.get('metadata'):
            metadata = json.loads(payload.get('metadata'))
    except json.JSONDecodeError as e:
        logger.error(f"File {data.get('id')} metadata JSONDecodeError")
        return True

    if not isinstance(metadata, dict):
        logger.info(f"File {data.get('id')} metadata is not dict type: {type(metadata)}")
        return True

    file_id = data.get("id", "")
    file_name =data.get("filename", "")
    callbacks = metadata.get("callbacks", [])

    if not check_supported_file_type(file_name):
        logger.info(f"not supported file type: {file_name}")
        return True

    file_info = parse_manager.file_api_get_file_info(file_id)
    if not file_info or "error" in file_info:
        logger.info(f"file_info not found for file_id: {file_id}")
        return True

    parser_context.register_user(str(data.get("cuid", "")))
    # 检查文件大小
    try:
        file_size_m = check_file_size(file_info)
    except BusinessError as e:
        logger.error(f"File {file_id} size check failed: {e}")
        parse_manager.callback_file_api(file_id, DOCUMENT_PARSE_FAIL, str(e))
        return True

    # 根据文件类型，大小进行分类
    contents = parse_manager.file_api_retrieve_file(file_id)
    # 检查文档准入标准
    group_id_analysis_info = None
    try:
        group_id_analysis_info = check_page_count(contents, file_info, file_size_m)
    except BusinessError as e:
        logger.error(f"File {data.get('id')} BusinessError: {e}")
        parse_manager.callback_file_api(file_id, DOCUMENT_PARSE_FAIL, str(e))
        return True

    # 计算groupId
    file_group_id = get_group_id(group_id_analysis_info)
    logger.info(f"计算groupId结果. file_id:{file_id} file_name:{file_name} file_group_id:{file_group_id}")

    if consumer_info['group_id'] == file_group_id:
        logger.info(f"parser开始解析. file_id:{file_id} file_group_id:{file_group_id}")
        file_meta = {
            "space_code": data.get("space_code", ""),
            "cuid": data.get("cuid", ""),
            "cu_name": data.get("cu_name", "")
        }
        file_info["file_meta"] = file_meta
        parse_manager.parse_result_layout_and_domtree(file_info, callbacks)
    return True



# 检查支持的文件类型，排除音频文件
def check_supported_file_type(file_name: str) -> bool:
    if "." not in file_name:
        return False
    file_extension = general_util.get_file_type(file_name)
    # 从配置文件读取支持的文件类型
    try:
        types_str = config.get('SUPPORTED_FILE_TYPES', 'types')
        supported_types = [file_type.strip() for file_type in types_str.split(',') if file_type.strip()]
        return file_extension in supported_types
    except Exception as e:
        raise ValueError(f"无法读取支持的文件类型配置: {e}")

# 根据文件大小和页数获取group_id
def get_group_id(group_id_analysis_info):
    file_size_m = group_id_analysis_info["file_size_m"]
    file_extension = group_id_analysis_info["file_extension"]
    page_count = group_id_analysis_info["page_count"]

    if file_extension in ["png", "jpeg", "jpg", "bmp"]:
        return GROUP_ID_IMAGE_TASK

    if file_extension in ["docx"]:
        return GROUP_ID_DOC_TASK

    if file_size_m > 2:  # 大于2Mb
        return GROUP_ID_LONG_TASK

    if page_count > 30:  # 大于30页
        return GROUP_ID_LONG_TASK

    return GROUP_ID_SHORT_TASK


# 检查文件大小和页数
def check_page_count(contents, file_info, file_size_m: float):
    file_id = file_info["id"]
    file_name = file_info["filename"]
    # 参数检验
    parse_manager.validate_parameters(file_name, contents)
    # 获取文件后缀
    file_extension = general_util.get_file_type(file_name)

    # 文件页数限制：小于5000页
    page_count = 0
    try:
        if file_extension == 'pptx':
            page_count = pptx_parser.get_page_count(contents)
        elif file_extension == 'pdf':
            page_count = pdf_parser.get_page_count(contents)
        elif file_extension == 'docx':
            paragraph_count = docx_parser.get_paragraph_count(contents)
            page_count = paragraph_count / 10  # docx文件无法直接拿到页数，先用每页段落数较大值预估
    except Exception as e:
        logger.error(f"文件页数检查失败. file_id:{file_id} file_name:{file_name} error:{e}")
        raise BusinessError(f"文件格式错误或损坏，无法解析")

    if page_count > 5000:
        logger.error(f"文件页数超出限制. file_id:{file_id} file_name:{file_name} page_count:{page_count}")
        raise BusinessError("文件页数超出限制，解析中止")

    group_id_analysis_info = {
        "file_size_m": file_size_m,
        "file_extension": file_extension,
        "page_count": page_count
    }
    return group_id_analysis_info