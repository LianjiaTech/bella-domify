from concurrent.futures import ThreadPoolExecutor, TimeoutError

from doc_parser.context import logger_context
from utils.kafka_tool import KafkaConsumer

logger = logger_context.get_logger()


class BaseListener(KafkaConsumer):
    _enable = True  # 是否可启动

    def __init__(self, instance_num, **task_config):
        if task_config['bootstrap_servers'] is None or task_config['topic'] is None or task_config['group_id'] is None:
            logger.info("Kafka配置不完整，无法创建Listener实例: bootstrap_servers=%s topic=%s group_id=%s",
                        task_config['bootstrap_servers'], task_config['topic'], task_config['group_id'])
            self._enable = False
        else:
            super().__init__(**task_config)
            # callback执行线程池，工作线程数设置需适当高于kafka消费线程数
            self.callback_executor = ThreadPoolExecutor(max_workers=3 * instance_num)

    @classmethod
    def get_instance(cls, instance_num: int):
        """
        使用get_instance方法创建时候必须实现一个无参的构造方法
        """
        instance_arr = []
        for i in range(instance_num):
            instance = cls(instance_num)
            if instance._enable:
                logger.info("创建kafka消费者 topic=%s group_id=%s 实例【%s】", instance.topic, instance.group_id, i)
                instance_arr.append(instance)
            else:
                logger.info("Listener %s 实例【%s】不可用，跳过创建", cls.__name__, i)

        return instance_arr

    def run_callback(self, payload, **kwargs) -> bool:
        future = self.callback_executor.submit(self.callback, payload, **kwargs)
        try:
            # 设置超时时间，单位为秒
            return future.result(timeout=self.callback_timeout)
        except TimeoutError:
            future.cancel()
            logger.warn("callback执行超时 consumer topic: [%s] message: %s", self.topic, payload)
            return False
