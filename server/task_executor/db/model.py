from datetime import datetime
from threading import Thread
from typing import Optional
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import scoped_session
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Enum,
    DECIMAL,
    DateTime,
    Boolean,
    UniqueConstraint,
    Index
)
from sqlalchemy.ext.declarative import declarative_base

from settings.ini_config import config

# 基础类
Base = declarative_base()

# sqlalchemy的mysql链接url
user_name = config.get('DATABASE', 'USERNAME')
password = config.get('DATABASE', 'PASSWORD')
host = config.get('DATABASE', 'HOST')
port = config.get('DATABASE', 'PORT')
database = config.get('DATABASE', 'DB')
url = f"mysql+pymysql://{user_name}:{password}@{host}:{port}/{database}?charset=utf8mb4"
# 创建引擎
engine = create_engine(
    url,
    # 超过链接池大小外最多创建的链接
    max_overflow=0,
    # 链接池大小
    pool_size=30,
    # 链接池中没有可用链接则最多等待的秒数，超过该秒数后报错
    pool_timeout=10,
    # 多久之后对链接池中的链接进行一次回收
    pool_recycle=1,
    # 查看原生语句（未格式化）
    echo=False,
    pool_pre_ping=True,
)


class DocumenParseTask(Base):
    __tablename__ = 'document_parse_task'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(128), nullable=False, comment='任务id')
    file_key = Column(String(255), nullable=False, comment='文件key(s3)')
    parse_result_file_key = Column(String(255), nullable=False, comment='解析结果文件key(s3)', default='')
    file_type = Column(Enum('pdf', 'word', 'other'), nullable=False, comment='文件类型')
    file_status = Column(Enum('wait', 'running', 'done', 'error', 'canceled'), nullable=False, comment='文件状态')
    create_time = Column(DateTime, nullable=False, comment='创建时间', default=datetime.now)
    update_time = Column(DateTime, nullable=False, comment='更新时间', default=datetime.now, onupdate=datetime.now)
    callback_url = Column(String(256), nullable=False, comment='回调地址', default='')

    def __repr__(self):
        return "<DocumenParseTask(task_id='%s', file_key='%s', file_type='%s', file_status='%s')>" % (
            self.task_id, self.file_key, self.file_type, self.file_status)


def create_task(*, task_id, file_key, file_type, callback_url):
    # 增加任务
    task = DocumenParseTask(
        task_id=task_id,
        file_key=file_key,
        file_type=file_type,
        file_status='wait',
        callback_url=callback_url
    )
    with Session(engine) as session:
        session.add(task)
        session.commit()


def get_wait_task() -> Optional[DocumenParseTask]:
    with Session(engine) as session:
        session.begin()
        task = (session.query(DocumenParseTask)
                .filter(DocumenParseTask.file_status == 'wait')
                .order_by(DocumenParseTask.create_time)
                .with_for_update()
                .first())
        if task is None:
            session.commit()
            return None
        else:
            print(f"get_task:{task.task_id}, {task.file_status},{datetime.now()}")
            update_task_status_by_id(task.task_id, 'running', session=session)
            session.expunge(task)
            session.commit()
            print(f"release transaction:{task.task_id} {datetime.now()}")
            return task


def update_task_status_by_id(task_id, status, *, session):
    (session.query(DocumenParseTask)
     .filter(DocumenParseTask.task_id == task_id)
     .update({'file_status': status}))


def upload_task_parse_res(task_id: str, parse_result_file_key: str):
    with Session(engine) as session:
        (session.query(DocumenParseTask)
         .filter(DocumenParseTask.task_id == task_id)
         .update({'file_status': 'done', 'parse_result_file_key': parse_result_file_key}))
        session.commit()


if __name__ == '__main__':
    # 增加任务
    # create_task(task_id='123fdvsaq2etr ', file_key='test', file_type='pdf')
    for i in range(3):
        Thread(target=get_wait_task).start()
