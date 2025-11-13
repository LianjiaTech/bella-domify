import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from doc_parser.context import logger_context
from server.workers.listeners.file_api_listener import (
    FileApiLongTaskListener, 
    FileApiShortTaskListener,
    FileApiImageTaskListener, 
    FileApiDocx2PdfTaskListener
)
from utils.kafka_tool import KafkaConsumer

logger = logger_context.get_logger()


class IsolationStateManager:
    """隔离状态管理器 - 管理被隔离业务空间的状态"""
    
    def __init__(self):
        self.isolated_spaces = set()
        self.lock = threading.RLock()
    
    def add_isolated_space(self, space_code: str):
        """添加被隔离的业务空间"""
        with self.lock:
            self.isolated_spaces.add(space_code)
            logger.info(f"Added isolated space: {space_code}")
    
    def remove_isolated_space(self, space_code: str):
        """移除被隔离的业务空间"""
        with self.lock:
            self.isolated_spaces.discard(space_code)
            logger.info(f"Removed isolated space: {space_code}")
    
    def is_space_isolated(self, space_code: str) -> bool:
        """检查业务空间是否被隔离"""
        with self.lock:
            return space_code in self.isolated_spaces
    
    def get_isolated_spaces(self) -> List[str]:
        """获取所有被隔离的业务空间"""
        with self.lock:
            return list(self.isolated_spaces)


class DynamicConsumerManager:
    """动态消费者管理器 - 负责动态创建和管理业务专属消费者"""
    
    def __init__(self):
        self.dynamic_consumers = {}  # 动态消费者注册表
        self.executor = None         # 动态消费者线程池
        self.lock = threading.Lock() # 线程安全锁
        self.initialized = False
        
        # 消费者类映射
        self.consumer_class_map = {
            'short': FileApiShortTaskListener,
            'long': FileApiLongTaskListener,
            'image': FileApiImageTaskListener,
            'docx': FileApiDocx2PdfTaskListener
        }
    
    def initialize(self):
        """初始化动态消费者管理器"""
        with self.lock:
            if not self.initialized:
                self.executor = ThreadPoolExecutor(max_workers=20)  # 动态消费者线程池
                self.initialized = True
                logger.info("Dynamic consumer manager initialized")
    
    def start_isolated_consumer(self, space_code: str, task_types: List[str], config: Dict) -> bool:
        """启动业务专属消费者组"""
        if not self.initialized:
            logger.error("Dynamic consumer manager not initialized")
            return False
            
        with self.lock:
            consumer_key = f"isolated_{space_code}"
            
            if consumer_key in self.dynamic_consumers:
                logger.warning(f"Consumer for space {space_code} already exists")
                return False
                
            # 为每种任务类型创建消费者
            consumers = []
            for task_type in task_types:
                consumer = self._create_isolated_consumer(space_code, task_type, config)
                if consumer:
                    consumers.append(consumer)
            
            if consumers:
                self.dynamic_consumers[consumer_key] = {
                    'consumers': consumers,
                    'space_code': space_code,
                    'created_at': time.time(),
                    'config': config
                }
                
                # 启动消费者
                self._start_consumers(consumers)
                logger.info(f"Started {len(consumers)} isolated consumers for space: {space_code}")
                return True
            else:
                logger.error(f"Failed to create any consumers for space: {space_code}")
                return False
    
    def isolate_business(self, space_code: str, task_type: str, max_workers: int = 3, callback_timeout: int = 300) -> bool:
        """便捷方法：为单个任务类型创建隔离消费者（用于静态配置）"""
        config = {
            'max_workers': max_workers,
            'callback_timeout': callback_timeout
        }
        
        return self.start_isolated_consumer(space_code, [task_type], config)
    
    def sync_consumers_with_config(self, config_manager) -> Dict[str, bool]:
        """根据配置管理器同步消费者状态"""
        results = {}
        
        try:
            # 获取当前配置中的隔离空间
            target_spaces = set(config_manager.get_isolated_spaces())
            current_spaces = set()
            
            with self.lock:
                # 获取当前运行中的隔离空间
                for consumer_key, info in self.dynamic_consumers.items():
                    if consumer_key.startswith('isolated_'):
                        current_spaces.add(info['space_code'])
            
            # 计算需要添加和移除的空间
            spaces_to_add = target_spaces - current_spaces
            spaces_to_remove = current_spaces - target_spaces
            spaces_to_check = target_spaces & current_spaces  # 可能需要更新配置的空间
            
            logger.info(f"Sync consumers: add={spaces_to_add}, remove={spaces_to_remove}, check={spaces_to_check}")
            
            # 移除不再需要的消费者
            for space_code in spaces_to_remove:
                success = self.stop_isolated_consumer(space_code)
                results[f"remove_{space_code}"] = success
            
            # 添加新的消费者
            for space_code in spaces_to_add:
                space_config = config_manager.get_space_config(space_code)
                if space_config:
                    success = self.start_isolated_consumer(
                        space_code,
                        space_config.get('task_types', ['short', 'long', 'image', 'docx']),
                        space_config
                    )
                    results[f"add_{space_code}"] = success
                else:
                    results[f"add_{space_code}"] = False
                    logger.error(f"No config found for space: {space_code}")
            
            # 检查现有消费者的配置是否需要更新
            for space_code in spaces_to_check:
                if self._should_update_consumer_config(space_code, config_manager):
                    # 重启消费者以应用新配置
                    self.stop_isolated_consumer(space_code)
                    space_config = config_manager.get_space_config(space_code)
                    if space_config:
                        success = self.start_isolated_consumer(
                            space_code,
                            space_config.get('task_types', ['short', 'long', 'image', 'docx']),
                            space_config
                        )
                        results[f"update_{space_code}"] = success
                    else:
                        results[f"update_{space_code}"] = False
                        
        except Exception as e:
            logger.error(f"Error syncing consumers with config: {e}")
            results["error"] = str(e)
            
        return results
    
    def _should_update_consumer_config(self, space_code: str, config_manager) -> bool:
        """检查消费者配置是否需要更新"""
        with self.lock:
            consumer_key = f"isolated_{space_code}"
            if consumer_key not in self.dynamic_consumers:
                return False
                
            current_config = self.dynamic_consumers[consumer_key]['config']
            target_config = config_manager.get_space_config(space_code)
            
            if not target_config:
                return False
                
            # 比较关键配置项
            key_fields = ['max_workers', 'callback_timeout', 'task_types']
            for field in key_fields:
                if current_config.get(field) != target_config.get(field):
                    logger.info(f"Config changed for {space_code}.{field}: {current_config.get(field)} -> {target_config.get(field)}")
                    return True
                    
            return False
    
    def stop_isolated_consumer(self, space_code: str) -> bool:
        """停止业务专属消费者组"""
        with self.lock:
            consumer_key = f"isolated_{space_code}"
            
            if consumer_key not in self.dynamic_consumers:
                logger.warning(f"No consumer found for space: {space_code}")
                return False
                
            consumer_info = self.dynamic_consumers.pop(consumer_key)
            consumers = consumer_info['consumers']
            
            # 停止所有消费者
            for consumer in consumers:
                try:
                    consumer.stop()
                except Exception as e:
                    logger.error(f"Error stopping consumer for space {space_code}: {e}")
                    
            logger.info(f"Stopped {len(consumers)} isolated consumers for space: {space_code}")
            return True
    
    def stop_all(self):
        """停止所有动态消费者"""
        with self.lock:
            spaces_to_stop = list(self.dynamic_consumers.keys())
            
        for consumer_key in spaces_to_stop:
            space_code = consumer_key.replace('isolated_', '')
            self.stop_isolated_consumer(space_code)
            
        # 关闭线程池
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("Dynamic consumer manager stopped")
    
    def get_status(self) -> Dict:
        """获取动态消费者状态"""
        with self.lock:
            status = {}
            for consumer_key, info in self.dynamic_consumers.items():
                space_code = info['space_code']
                status[space_code] = {
                    'consumer_count': len(info['consumers']),
                    'created_at': info['created_at'],
                    'config': info['config']
                }
            return status
    
    def _create_isolated_consumer(self, space_code: str, task_type: str, config: Dict) -> Optional[KafkaConsumer]:
        """创建业务专属消费者"""
        consumer_class = self.consumer_class_map.get(task_type)
        if not consumer_class:
            logger.error(f"Unknown task type: {task_type}")
            return None
        
        try:
            # 创建专属消费者实例
            consumer = consumer_class._create_isolated_instance(
                space_code=space_code,
                instance_num=1,
                max_workers=config.get('max_workers', 3),
                callback_timeout=config.get('callback_timeout', 5 * 60)
            )
            
            if consumer and consumer._enable:
                logger.info(f"Created isolated consumer for space={space_code} task_type={task_type}")
                return consumer
            else:
                logger.error(f"Failed to create consumer for space={space_code} task_type={task_type}")
                return None
                
        except Exception as e:
            logger.error(f"Exception creating consumer for {space_code}-{task_type}: {e}")
            return None
    
    def _start_consumers(self, consumers: List[KafkaConsumer]):
        """启动消费者列表"""
        for consumer in consumers:
            try:
                self.executor.submit(consumer.consume_messages)
                logger.info(f"Started consumer topic={consumer.topic} group_id={consumer.group_id}")
            except Exception as e:
                logger.error(f"Failed to start consumer {consumer.group_id}: {e}")


# 全局实例
isolation_state = IsolationStateManager()
dynamic_manager = DynamicConsumerManager()


def sync_with_s3_config(config_manager):
    """与S3配置同步的便捷函数"""
    return dynamic_manager.sync_consumers_with_config(config_manager)


def is_space_isolated(space_code: str) -> bool:
    """检查业务空间是否被隔离"""
    return isolation_state.is_space_isolated(space_code)


def isolate_business(space_code: str, config: Optional[Dict] = None) -> bool:
    """隔离指定业务空间（完整模式）"""
    default_config = {
        'max_workers': 3,
        'callback_timeout': 5 * 60,
        'task_types': ['short', 'long', 'image', 'docx']
    }
    
    final_config = {**default_config, **(config or {})}
    
    # 启动专属消费者
    success = dynamic_manager.start_isolated_consumer(
        space_code, 
        final_config['task_types'], 
        final_config
    )
    
    if success:
        # 更新隔离状态
        isolation_state.add_isolated_space(space_code)
        logger.info(f"Successfully isolated business: {space_code}")
    else:
        logger.error(f"Failed to isolate business: {space_code}")
    
    return success


def restore_business(space_code: str) -> bool:
    """恢复业务空间到通用处理"""
    # 停止专属消费者
    success = dynamic_manager.stop_isolated_consumer(space_code)
    
    if success:
        # 移除隔离状态
        isolation_state.remove_isolated_space(space_code)
        logger.info(f"Successfully restored business: {space_code}")
    else:
        logger.error(f"Failed to restore business: {space_code}")
    
    return success


def get_isolation_status() -> Dict:
    """获取当前隔离状态"""
    return {
        'isolated_spaces': isolation_state.get_isolated_spaces(),
        'active_consumers': dynamic_manager.get_status()
    }