import json
import threading
import time
from concurrent.futures import Future

from confluent_kafka import Producer, KafkaError, Consumer

from doc_parser.context import logger_context
from utils.inspect_util import has_parameter

logger = logger_context.get_logger()

# 默认最大重试次数
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
                 callback_timeout,
                 producer=None,
                 # callback_timeout + err_retry_max 需小于 retry_interval！防止重平衡
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
        self.consumer.subscribe([self.topic])
        self.callback = callback
        self.err_retry_max = err_retry_max
        self.retry_interval = retry_interval
        self.__closed = False
        self.lock = threading.Lock()
        self.callback_timeout = callback_timeout
        self.producer = producer

    def consume_messages(self):
        """
        三次重试，失败后打印错误日志，研发查看原因，手动补偿
        """
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
                    message_value = msg.value().decode("utf-8")
                    logger.info("Received topic: [%s] partition:[%s] message: %s",
                                self.topic, msg.partition(), message_value)
                    payload: dict = json.loads(message_value)
                    err_cnt = payload.get('reconsume_times', 0)
                    try:
                        # 传递重试次数，仿照rocketMQ，取名，各自回调视情况需要接收
                        kwargs = {}
                        if has_parameter(self.callback, "reconsume_times"):
                            kwargs["reconsume_times"] = err_cnt

                        if has_parameter(self.callback, "consumer_info"):
                            kwargs["consumer_info"] = {'topic': self.topic, 'group_id': self.group_id}

                        if self.run_callback(payload, **kwargs):
                            # 手动提交偏移量
                            self.consumer.commit(msg)
                            logger.info("consumer topic: [%s] partition:[%s] message: %s 消费成功",
                                        self.topic, msg.partition(), message_value)
                        else:
                            err_cnt += 1
                            logger.info("consumer topic: [%s] partition:[%s] message: %s  retry=%s",
                                        self.topic, msg.partition(), message_value, err_cnt)

                    except Exception as e:
                        err_cnt += 1
                        logger.warn("异常 consumer  topic: [%s] partition:[%s] message: %s  retry=%s",
                                    self.topic, msg.partition(), message_value, err_cnt, exc_info=e, stack_info=True)
                        # 如果是0则不会引入任何延迟
                        time.sleep(self.retry_interval)

                    if err_cnt >= self.err_retry_max:
                        logger.error("consumer fail topic: [%s] partition:[%s] 需要研发关注是否需要补偿: %s",
                                     self.topic, msg.partition(), message_value)
                        self.consumer.commit(msg)
                    elif payload.get('reconsume_times', 0) != err_cnt:
                        # 本次消费执行失败，重新发送kafka消息
                        payload.update({'reconsume_times': err_cnt})
                        self.reconsume_messages(json.dumps(payload))
                        self.consumer.commit(msg)

        except KeyboardInterrupt:
            logger.error("用户中断")
        except KafkaError as e:
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
