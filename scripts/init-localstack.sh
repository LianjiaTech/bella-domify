#!/bin/bash

echo "Initializing LocalStack S3..."

# 等待LocalStack完全启动
sleep 5

# 创建S3 bucket
aws --endpoint-url=http://localhost:4566 s3 mb s3://test-bucket

# 验证bucket是否创建成功
aws --endpoint-url=http://localhost:4566 s3 ls

echo "LocalStack S3 initialization completed!"