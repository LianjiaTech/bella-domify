import json
import threading
import time
from concurrent.futures import Future

from confluent_kafka import Consumer, KafkaError, KafkaException, Producer, TopicPartition

from doc_parser.context import logger_context
from utils.inspect_util import has_parameter

logger = logger_context.get_logger()

# 默认最多处理三次，包含首次处理
DEFAULT_ERR_RETRY_MAX = 3
# 默认重试间隔，0没有间隔
DEFAULT_RETRY_INTERVAL = 0


class KafkaProducer:

    def __init__(self, bootstrap_servers, topic):
        self.producer = Producer(
            {
                'bootstrap.servers': bootstrap_servers,
                'acks': 'all',
                'retries': 9,
                'retry.backoff.ms': 1000,
            }
        )
        self._topic = topic

    @property
    def topic(self):
        return self._topic

    def __delivery_report(self, future, err, msg):
        if err is not None:
            future.set_result(False)
            logger.error("Message delivery failed: error=%s, msg=%s", err, msg)
        else:
            logger.info("发送消息成功  topic: [%s] partition:[%s] message: %s", msg.topic(), msg.partition(),
                        msg.value().decode("utf-8"))
            future.set_result(True)

    def sync_send_message(self, message) -> bool:
        future = Future()
        self.producer.produce(topic=self._topic, value=message,
                              callback=lambda err, msg: self.__delivery_report(future, err, msg))
        self.producer.flush()
        return future.result()  # 等待结果


class KafkaConsumer:
    def __init__(self,
                 bootstrap_servers,
                 group_id,
                 topic,
                 callback,
                 callback_timeout=None,  # 兼容旧调用，回调不再设置总超时
                 producer=None,
                 err_retry_max=DEFAULT_ERR_RETRY_MAX,
                 retry_interval=DEFAULT_RETRY_INTERVAL,
                 **kwargs):
        base_conf = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',  # 可以是 'earliest', 'latest', 'none'
            'enable.auto.commit': False,  # 禁用自动提交
        }
        base_conf.update(kwargs)

        self.consumer = Consumer(base_conf)
        self.topic = topic
        self.group_id = group_id
        self.callback = callback
        self.err_retry_max = err_retry_max
        self.retry_interval = retry_interval
        self.__closed = False
        self.lock = threading.Lock()
        self.producer = producer
        self._failed_offsets = {}
        self.consumer.subscribe([self.topic], on_revoke=self._clear_failed_offsets)

    def consume_messages(self):
        """消费失败时从原位点重读，耗尽后提交位点并继续消费。"""
        try:
            while True:
                with self.lock:
                    if self.__closed:
                        break
                    msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info("consume_messages PARTITION_EOF topic=%s partition=%s code=%s ",
                                    self.topic, msg.partition(), msg.error().code())
                    else:
                        logger.error("consume_messages error topic=%s partition=%s code=%s message: %s",
                                     self.topic, msg.partition(), msg.error().code(),
                                     msg.value().decode("utf-8") if msg.value() else "None")
                else:
                    partition = (msg.topic(), msg.partition())
                    offset = msg.offset()
                    failure = self._failed_offsets.get(partition)
                    if failure is not None:
                        failed_offset, err_cnt = failure
                        # 防止同分区的后续消息越过失败位点。
                        if offset != failed_offset:
                            self.consumer.seek(TopicPartition(*partition, failed_offset))
                            continue

                    message_value = msg.value().decode("utf-8")
                    logger.info("Received topic: [%s] partition:[%s] message: %s",
                                self.topic, msg.partition(), message_value)
                    payload: dict = json.loads(message_value)
                    
                    # 检查是否应该处理此消息（消息过滤）
                    if (failure is None and hasattr(self, 'should_process_message')
                            and not self.should_process_message(payload)):
                        # 不处理，但要提交offset避免重复消费
                        self.consumer.commit(msg)
                        logger.info(
                            "Message filtered, skipping: topic=[%s] partition=[%s] space_code=%s consumer_group=%s",
                            self.topic, msg.partition(), payload.get('data', {}).get('space_code', ''), self.group_id)
                        continue
                    
                    if failure is None:
                        err_cnt = payload.get('reconsume_times', 0)
                    kwargs = {}
                    if has_parameter(self.callback, "reconsume_times"):
                        kwargs["reconsume_times"] = err_cnt
                    if has_parameter(self.callback, "consumer_info"):
                        kwargs["consumer_info"] = {'topic': self.topic, 'group_id': self.group_id}

                    try:
                        succeeded = self.run_callback(payload, **kwargs)
                    except Exception:
                        logger.exception("Kafka 回调异常 topic=%s partition=%s offset=%s group=%s",
                                         *partition, offset, self.group_id)
                        succeeded = False

                    if succeeded:
                        self.consumer.commit(msg)
                        self._failed_offsets.pop(partition, None)
                        logger.info("consumer topic: [%s] partition:[%s] message: %s 消费成功 consumer_group=%s",
                                    self.topic, msg.partition(), message_value, self.group_id)
                        continue

                    err_cnt += 1
                    if err_cnt >= self.err_retry_max:
                        self.consumer.commit(msg)
                        self._failed_offsets.pop(partition, None)
                        logger.error("Kafka 消费失败，达到处理上限，提交位点并跳过消息 "
                                     "topic=%s partition=%s offset=%s group=%s attempts=%s",
                                     *partition, offset, self.group_id, err_cnt)
                        continue

                    if self.retry_interval > 0:
                        time.sleep(self.retry_interval)
                    self.consumer.seek(TopicPartition(*partition, offset))
                    self._failed_offsets[partition] = (offset, err_cnt)
                    logger.warning("Kafka 消费失败，将从原位点重试 topic=%s partition=%s offset=%s group=%s attempts=%s",
                                   *partition, offset, self.group_id, err_cnt)

        except KeyboardInterrupt:
            logger.error("用户中断")
        except KafkaException as e:
            logger.error("Kafka 错误: %s", e)
        except Exception as e:
            if e.args and e.args[0] == 'Consumer closed' and self.__closed:
                logger.info("Consumer closed topic: [%s]", self.topic)
            else:
                logger.error("Exception 错误: topic: [%s] error: %s", self.topic, e)
        finally:
            if not self.__closed:
                logger.info("workers topic = %s final close", self.topic)
                self.consumer.close()

    def _clear_failed_offsets(self, _consumer, partitions):
        for partition in partitions:
            self._failed_offsets.pop((partition.topic, partition.partition), None)

    def stop(self):
        with self.lock:
            if not self.__closed:
                logger.info("workers  topic = %s stop close", self.topic)
                self.__closed = True
                self.consumer.close()

    def run_callback(self, payload, **kwargs) -> bool:
        return self.callback(payload, **kwargs)

    def reconsume_messages(self, message_value):
        logger.info("reconsume message topic: [%s] message: %s", self.topic, message_value)
        if self.producer:
            self.producer.sync_send_message(message_value)
