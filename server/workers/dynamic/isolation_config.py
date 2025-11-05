"""
基于S3的动态隔离配置管理器
支持配置热更新和版本管理
"""

import json
import threading
import time
from typing import Dict, List, Optional, Set
from datetime import datetime

from doc_parser.context import logger_context
from utils import s3

logger = logger_context.get_logger()


class IsolationConfigManager:
    """基于S3的隔离配置管理器"""
    
    def __init__(self, config_key: str = "isolation/config.json", poll_interval: int = 30):
        """
        初始化S3配置管理器
        
        Args:
            config_key: S3中配置文件的key
            poll_interval: 配置轮询间隔(秒)
        """
        self.config_key = config_key
        self.poll_interval = poll_interval
        
        # 配置缓存
        self._current_config = None
        self._current_version = None
        self._last_check_time = 0
        
        # 线程安全
        self._lock = threading.RLock()
        self._polling_thread = None
        self._stop_polling = False
        
        # 配置变更回调
        self._change_callbacks = []
        
        # 默认配置
        self._default_config = {
            "spaces": {},
            "default_config": {
                "max_workers": 3,
                "callback_timeout": 300,
                "task_types": ["short", "long", "image", "docx"]
            },
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat()
        }
    
    def start_polling(self):
        """启动配置轮询"""
        with self._lock:
            if self._polling_thread and self._polling_thread.is_alive():
                logger.warning("Polling thread already running")
                return
                
            # 初始加载配置
            self._load_config_from_s3()
            
            # 启动轮询线程
            self._stop_polling = False
            self._polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
            self._polling_thread.start()
            logger.info(f"Started S3 config polling with interval {self.poll_interval}s")
    
    def stop_polling(self):
        """停止配置轮询"""
        with self._lock:
            self._stop_polling = True
            if self._polling_thread:
                self._polling_thread.join(timeout=5)
                logger.info("Stopped S3 config polling")
    
    def _polling_loop(self):
        """配置轮询循环"""
        while not self._stop_polling:
            try:
                # 检查配置更新
                if self._check_and_update_config():
                    logger.info("Configuration updated from S3")
                    
                # 等待下次轮询
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in config polling: {e}")
                time.sleep(min(60, self.poll_interval * 2))  # 错误时延长等待
    
    def _check_and_update_config(self) -> bool:
        """检查并更新配置，返回是否有变更"""
        try:
            # 从S3获取配置
            new_config = self._fetch_config_from_s3()
            if not new_config:
                return False
                
            with self._lock:
                new_version = new_config.get("version", "unknown")
                
                # 检查版本是否变更
                if new_version != self._current_version:
                    old_config = self._current_config
                    self._current_config = new_config
                    self._current_version = new_version
                    self._last_check_time = time.time()
                    
                    # 触发变更回调
                    self._trigger_change_callbacks(old_config, new_config)
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking config update: {e}")
            return False
    
    def _load_config_from_s3(self):
        """初次加载配置"""
        try:
            config = self._fetch_config_from_s3()
            if config:
                with self._lock:
                    self._current_config = config
                    self._current_version = config.get("version", "unknown")
                    self._last_check_time = time.time()
                    logger.info(f"Loaded initial config from S3, version: {self._current_version}")
            else:
                # 使用默认配置并上传到S3
                self._use_default_config()
        except Exception as e:
            logger.error(f"Error loading initial config: {e}")
            self._use_default_config()
    
    def _use_default_config(self):
        """使用默认配置"""
        with self._lock:
            self._current_config = self._default_config.copy()
            self._current_version = self._default_config["version"]
            self._last_check_time = time.time()
            logger.info("Using default isolation config")
            
        # 尝试上传默认配置到S3
        try:
            self.upload_config(self._default_config)
            logger.info("Uploaded default config to S3")
        except Exception as e:
            logger.error(f"Failed to upload default config to S3: {e}")
    
    def _fetch_config_from_s3(self) -> Optional[Dict]:
        """从S3获取配置"""
        try:
            config_content = s3.get_file_text_content(self.config_key)
            config_data = json.loads(config_content)
            
            # 验证配置格式
            if self._validate_config(config_data):
                return config_data
            else:
                logger.error("Invalid config format from S3")
                return None
                
        except Exception as e:
            # 配置文件不存在或格式错误
            logger.warning(f"Could not fetch config from S3: {e}")
            return None
    
    def _validate_config(self, config: Dict) -> bool:
        """验证配置格式"""
        try:
            required_keys = ["spaces", "default_config"]
            for key in required_keys:
                if key not in config:
                    logger.error(f"Missing required key in config: {key}")
                    return False
                    
            # 验证默认配置
            default_config = config["default_config"]
            if not all(k in default_config for k in ["max_workers", "callback_timeout", "task_types"]):
                logger.error("Invalid default_config format")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Config validation error: {e}")
            return False
    
    def upload_config(self, config: Dict) -> bool:
        """上传配置到S3"""
        try:
            # 添加时间戳和版本
            config_to_upload = config.copy()
            config_to_upload["last_updated"] = datetime.now().isoformat()
            if "version" not in config_to_upload:
                config_to_upload["version"] = "1.0.0"
                
            # 上传到S3
            s3.upload_dict_content(config_to_upload, self.config_key)
            logger.info(f"Uploaded config to S3: {self.config_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload config to S3: {e}")
            return False
    
    def get_isolated_spaces(self) -> List[str]:
        """获取需要隔离的业务空间列表"""
        with self._lock:
            if not self._current_config:
                return []
            return list(self._current_config.get("spaces", {}).keys())
    
    def get_space_config(self, space_code: str) -> Optional[Dict]:
        """获取业务空间配置"""
        with self._lock:
            if not self._current_config:
                return None
                
            spaces_config = self._current_config.get("spaces", {})
            space_config = spaces_config.get(space_code)
            
            if not space_config:
                return None
                
            # 合并默认配置
            default_config = self._current_config.get("default_config", {})
            final_config = {**default_config, **space_config}
            
            return final_config
    
    def is_space_isolated(self, space_code: str) -> bool:
        """检查业务空间是否被配置为隔离"""
        return space_code in self.get_isolated_spaces()
    
    def get_full_config(self) -> Optional[Dict]:
        """获取完整配置"""
        with self._lock:
            return self._current_config.copy() if self._current_config else None
    
    def add_change_callback(self, callback):
        """添加配置变更回调函数"""
        self._change_callbacks.append(callback)
    
    def _trigger_change_callbacks(self, old_config: Optional[Dict], new_config: Dict):
        """触发配置变更回调"""
        for callback in self._change_callbacks:
            try:
                callback(old_config, new_config)
            except Exception as e:
                logger.error(f"Error in change callback: {e}")
    
    def get_config_changes(self, old_config: Optional[Dict], new_config: Dict) -> Dict[str, Set[str]]:
        """分析配置变更，返回需要添加和移除的业务空间"""
        old_spaces = set()
        new_spaces = set()
        
        if old_config:
            old_spaces = set(old_config.get("spaces", {}).keys())
        if new_config:
            new_spaces = set(new_config.get("spaces", {}).keys())
            
        return {
            "added": new_spaces - old_spaces,
            "removed": old_spaces - new_spaces,
            "modified": new_spaces & old_spaces  # 可能配置参数发生变化的空间
        }


# 全局S3配置管理器实例
isolation_config_manager = IsolationConfigManager()