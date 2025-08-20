from doc_parser.dom_parser.provider.parse_result_cache_provider import ParseResultCacheProvider
from utils.cache import get_s3_parse_result, upload_s3_parse_result


class S3ParseResultCacheProvider(ParseResultCacheProvider):
    def get_parse_result(self, task_id, parse_type=""):
        return get_s3_parse_result(task_id, parse_type)

    def upload_parse_result(self, task_id, parse_result, parse_type):
        return upload_s3_parse_result(task_id, parse_result, parse_type)