#!/bin/bash

# 重启脚本
echo "🔄 重启 Phish Aggregator..."

# 先停止
./stop.sh

# 等待一下
sleep 1

# 再启动
./start.sh