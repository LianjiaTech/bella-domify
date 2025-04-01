#!/bin/bash

VERSION="1.0"

# 1. 在本地构建镜像
docker build -f ./Dockerfile-ke -t=bj-harbor01.ke.com/aistudio-ait/document_parse:${VERSION} .

# 启动 docker，本地验证
# docker run -t -i bj-harbor01.ke.com/aistudio-ait/document_parse:${VERSION} /bin/bash

# 2. 登陆仓库
docker login bj-harbor01.ke.com -u '<user>' -p <password>
# 3. 推送
docker push bj-harbor01.ke.com/aistudio-ait/document_parse:"${VERSION}"