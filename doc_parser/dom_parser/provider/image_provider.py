import io
import logging
from abc import ABC, abstractmethod

from PIL import Image


# 定义 Provider 接口
class ImageStorageProvider(ABC):
    @abstractmethod
    def upload(self, image: bytes) -> str:
        """上传图片并返回唯一标识"""
        raise NotImplementedError("子类必须实现 upload 方法")

    @abstractmethod
    def download(self, file_key: str) -> bytes:
        """根据 ID 下载文件"""
        raise NotImplementedError("子类必须实现 download 方法")

    def get_pic_url_and_ocr(self, image: bytes, user: str) -> tuple:
        """
        获取图片的URL和OCR文本
        :param image: 图片文件的字节流
        :param user: 用户标识，用于OCR处理
        :return: (图片URL, OCR文本)
        """

        def is_image_large_enough(buf_data, min_size=28):
            """
            检查图像的宽度和高度是否大于指定的最小尺寸。

            参数:
            - buf_data: 图像的二进制数据。
            - min_size: 最小尺寸（默认值为28）。

            返回:
            - 布尔值：如果图像的宽度和高度都大于min_size，则返回True；否则返回False。
            """
            try:
                with Image.open(io.BytesIO(buf_data)) as img:
                    width, height = img.size
                    return width > min_size and height > min_size
            except Exception as e:
                logging.warning(f"检查图像尺寸失败: {e}")
                return False
        image_url = ""
        from doc_parser.dom_parser.parsers.pdf.common.ocr import llm_image2text
        try:
            file_key = self.upload(image)
            image_url = self.download(file_key)
            if is_image_large_enough(image):
                ocr_text = llm_image2text(image_url, user)
            else:
                ocr_text = ""
        except Exception as e:
            logging.error(f"pic_parser Exception occurred: {e}")
            ocr_text = ""

        return image_url, ocr_text