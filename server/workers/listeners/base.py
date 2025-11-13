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
            self.space_filter = None  # 业务空间过滤器

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

    def set_space_filter(self, space_code: str):
        """设置业务空间过滤器"""
        self.space_filter = space_code
        logger.info(f"Set space filter to: {space_code} for consumer {self.group_id}")
    
    def should_process_message(self, message_data: dict) -> bool:
        """检查是否应该处理此消息"""
        # 导入这里放在方法内避免循环导入
        from server.workers.dynamic.dynamic_manager import is_space_isolated
        
        message_space = message_data.get('data', {}).get('space_code', '')
        
        if self.space_filter is None:
            # 通用消费者：处理未被隔离的消息
            return not is_space_isolated(message_space)
        else:
            # 专属消费者：只处理指定space的消息
            return message_space == self.space_filter
    
    @classmethod
    def _create_isolated_instance(cls, space_code: str, instance_num: int = 1, 
                                  max_workers: int = 3, callback_timeout: int = 300):
        """创建业务专属消费者实例"""
        try:
            # 获取原始配置
            original_config = cls._get_base_config()
            
            # 修改配置用于专属消费者
            isolated_config = original_config.copy()
            isolated_config['group_id'] = f"{original_config['group_id']}_isolated_{space_code}"
            isolated_config['callback_timeout'] = callback_timeout
            
            # 创建实例
            instance = cls.__new__(cls)
            if isolated_config['bootstrap_servers'] is None or isolated_config['topic'] is None:
                logger.info("Kafka配置不完整，无法创建专属Listener实例")
                instance._enable = False
                return instance
            
            # 手动初始化
            KafkaConsumer.__init__(instance, **isolated_config)
            instance.callback_executor = ThreadPoolExecutor(max_workers=max_workers)
            instance.space_filter = space_code
            instance._enable = True
            
            logger.info(f"Created isolated consumer: topic={instance.topic} group_id={instance.group_id} space={space_code}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create isolated instance for {space_code}: {e}")
            instance = cls.__new__(cls)
            instance._enable = False
            return instance
    
    def run_callback(self, payload, **kwargs) -> bool:
        future = self.callback_executor.submit(self.callback, payload, **kwargs)
        try:
            # 设置超时时间，单位为秒
            return future.result(timeout=self.callback_timeout)
        except TimeoutError:
            future.cancel()
            logger.warn("callback执行超时 consumer topic: [%s] message: %s", self.topic, payload)
            return False
