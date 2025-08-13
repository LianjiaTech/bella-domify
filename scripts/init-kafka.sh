#!/bin/bash

echo "Initializing Kafka topics..."

# 等待Kafka完全启动
echo "Waiting for Kafka to be ready..."
cub kafka-ready -b kafka:29092 1 30

# 创建bella-file-broadcast主题
echo "Creating topic: bella-file-broadcast"
kafka-topics --create --if-not-exists --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --topic bella-file-broadcast
# 验证主题是否创建成功
echo "Listing all topics:"
kafka-topics --list --bootstrap-server kafka:29092

echo "Kafka topics initialization completed!"