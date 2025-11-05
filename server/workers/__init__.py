from concurrent.futures import ThreadPoolExecutor
from typing import List

from doc_parser.context import logger_context
from server.workers.listeners.file_api_listener import FileApiLongTaskListener, FileApiShortTaskListener, \
    FileApiImageTaskListener, FileApiDocx2PdfTaskListener
from server.workers.dynamic.dynamic_manager import dynamic_manager
from utils.kafka_tool import KafkaConsumer

logger = logger_context.get_logger()

consumers: List[KafkaConsumer] = []
consumers.extend(FileApiLongTaskListener.get_instance(1))
consumers.extend(FileApiShortTaskListener.get_instance(1))
consumers.extend(FileApiImageTaskListener.get_instance(1))
consumers.extend(FileApiDocx2PdfTaskListener.get_instance(1))

# 线程池最大工作线程数
executor = None
if len(consumers) > 0:
    executor = ThreadPoolExecutor(max_workers=len(consumers))


def start_workers():
    """启动消费者工作进程"""
    # 启动原有的通用消费者
    for i, consumer in enumerate(consumers):
        logger.info("启动kafka消费者 topic=%s group_id=%s ", consumer.topic, consumer.group_id)
        executor.submit(consumer.consume_messages)
    
    # 初始化动态消费者管理器
    dynamic_manager.initialize()
    logger.info("Dynamic consumer manager initialized")
    
    # 启动S3配置管理器
    _start_config_manager()
    logger.info("S3 isolation config manager started")


def stop_workers():
    """停止消费者工作进程"""
    # 停止S3配置管理器
    try:
        from server.workers.dynamic.isolation_config import isolation_config_manager
        isolation_config_manager.stop_polling()
    except Exception as e:
        logger.error(f"Error stopping S3 config manager: {e}")
    
    # 停止通用消费者
    for consumer in consumers:
        consumer.stop()
        
    # 停止所有动态消费者
    dynamic_manager.stop_all()
    
    # 关闭线程池
    if executor:
        executor.shutdown()


def _start_config_manager():
    """启动S3配置管理器并设置变更回调"""
    from server.workers.dynamic.isolation_config import isolation_config_manager
    from server.workers.dynamic.dynamic_manager import sync_with_s3_config
    
    # 添加配置变更回调
    isolation_config_manager.add_change_callback(_on_config_changed)
    
    # 启动轮询
    isolation_config_manager.start_polling()
    
    # 初始同步一次
    try:
        results = sync_with_s3_config(isolation_config_manager)
        logger.info(f"Initial S3 config sync results: {results}")
    except Exception as e:
        logger.error(f"Error in initial S3 config sync: {e}")


def _on_config_changed(old_config, new_config):
    """配置变更回调函数"""
    try:
        from server.workers.dynamic.isolation_config import isolation_config_manager
        from server.workers.dynamic.dynamic_manager import sync_with_s3_config
        
        logger.info("S3 configuration changed, syncing consumers...")
        
        # 分析配置变更
        changes = isolation_config_manager.get_config_changes(old_config, new_config)
        logger.info(f"Config changes detected: {changes}")
        
        # 同步消费者
        results = sync_with_s3_config(isolation_config_manager)
        logger.info(f"Consumer sync results: {results}")
        
    except Exception as e:
        logger.error(f"Error handling config change: {e}")


__all__ = ['start_workers', 'stop_workers']
