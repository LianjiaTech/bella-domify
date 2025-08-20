from doc_parser.dom_parser.provider.image_provider import ImageStorageProvider
from utils import s3


class S3ImageStorageProvider(ImageStorageProvider):

    def upload(self, image: bytes) -> str:
        return s3.upload_file(stream=image)

    def download(self, file_key: str) -> bytes:
        return s3.get_file_url(file_key)