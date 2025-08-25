from concurrent.futures import ThreadPoolExecutor
from typing import List

from doc_parser.context import logger_context
from server.workers.listeners.file_api_listener import FileApiLongTaskListener, FileApiShortTaskListener, \
    FileApiImageTaskListener, FileApiDocTaskListener
from utils.kafka_tool import KafkaConsumer

logger = logger_context.get_logger()

consumers: List[KafkaConsumer] = []
consumers.extend(FileApiLongTaskListener.get_instance(1))
consumers.extend(FileApiShortTaskListener.get_instance(1))
consumers.extend(FileApiImageTaskListener.get_instance(1))
consumers.extend(FileApiDocTaskListener.get_instance(1))

# 线程池最大工作线程数
executor = None
if len(consumers) > 0:
    executor = ThreadPoolExecutor(max_workers=len(consumers))


def start_workers():
    # 提交任务到线程池
    for i, consumer in enumerate(consumers):
        logger.info("启动kafka消费者 topic=%s group_id=%s ", consumer.topic, consumer.group_id)
        executor.submit(consumer.consume_messages)


def stop_workers():
    for consumer in consumers:
        consumer.stop()
    if executor:
        executor.shutdown()


__all__ = ['start_workers', 'stop_workers']
