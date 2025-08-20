from typing import Optional
import os
import configparser
from pathlib import Path

from pydantic import BaseModel

class PaodingConfig(BaseModel):
    """
    配置类，用于存储Paoding相关的配置。
    """
    app_id: str
    user: str
    secret_key: str


class UnstructuredConfig(BaseModel):
    """
    配置类，用于存储Unstructured相关的配置。
    """
    api_key: str
    server_url: str


class LlamaparseConfig(BaseModel):
    """
    配置类，用于存储Llamaparse相关的配置。
    """
    api_key: str


class ChunkrConfig(BaseModel):
    """
    配置类，用于存储Chunkr相关的配置。
    """
    api_key: str



class EvaluationConfig(BaseModel):
    paodingConfig: Optional[PaodingConfig] = None
    unstructuredConfig: Optional[UnstructuredConfig] = None
    llamaparseConfig: Optional[LlamaparseConfig] = None
    chunkrConfig: Optional[ChunkrConfig] = None

    @classmethod
    def from_ini(cls, ini_path=None) -> 'EvaluationConfig':
        """
        从ini文件加载配置

        Args:
            ini_path: ini文件路径，如果为None，则使用默认路径

        Returns:
            EvaluationConfig: 配置对象
        """
        if ini_path is None:
            # 默认路径为evaluation目录下的evaluation.ini
            current_dir = Path(__file__).parent.parent
            ini_path = os.path.join(current_dir, 'evaluation.ini')

        config = configparser.ConfigParser()
        config.read(ini_path)

        # 创建配置对象
        evaluation_config = cls()

        # 加载Paoding配置
        if 'Paoding' in config:
            paoding_config = PaodingConfig(
                app_id=config['Paoding'].get('app_id', ''),
                user=config['Paoding'].get('user', ''),
                secret_key=config['Paoding'].get('secret_key', '')
            )
            evaluation_config.paodingConfig = paoding_config

        # 加载Unstructured配置
        if 'Unstructured' in config:
            unstructured_config = UnstructuredConfig(
                api_key=config['Unstructured'].get('api_key', ''),
                server_url=config['Unstructured'].get('server_url', '')
            )
            evaluation_config.unstructuredConfig = unstructured_config

        # 加载Llamaparse配置
        if 'Llamaparse' in config:
            llamaparse_config = LlamaparseConfig(
                api_key=config['Llamaparse'].get('api_key', '')
            )
            evaluation_config.llamaparseConfig = llamaparse_config

        # 加载Chunkr配置
        if 'Chunkr' in config:
            chunkr_config = ChunkrConfig(
                api_key=config['Chunkr'].get('api_key', '')
            )
            evaluation_config.chunkrConfig = chunkr_config

        return evaluation_config

