FROM python:3.9.19-slim AS base

RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware " >/etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware " >>/etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware " >>/etc/apt/sources.list && \
    echo "deb https://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware " >>/etc/apt/sources.list \
    && rm -rf /etc/apt/sources.list.d/*

RUN apt-get update \
    && apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config libgl1-mesa-glx libglib2.0-0 unoconv\
    && apt-get install -y bash curl wget vim \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/usr/lib/python3/dist-packages/:$PYTHONPATH

# 设置 Python 包源
COPY requirements.txt .
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple
RUN pip install -r requirements.txt

# 复制项目文件
COPY doc_parser/ ./doc_parser/
COPY server/ ./server/
COPY services/ ./services/
COPY settings/ ./settings/
COPY utils/ ./utils/
COPY resource/ ./resource/

# 设置时区
RUN rm -rf /etc/localtime
RUN ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# 设置 UNO_PATH 环境变量
ENV PYTHONPATH=/usr/lib/python3/dist-packages/:$PYTHONPATH

EXPOSE 8080

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
