#!/bin/bash

# 一键启动脚本
echo "🚀 启动 Phish Aggregator..."

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建：python -m venv .venv"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查端口是否被占用
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口8000已被占用，尝试停止现有进程..."
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    sleep 2
fi

# 启动服务
echo "🔧 启动后端服务..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 3

# 检查服务状态
if curl -s http://localhost:8000 >/dev/null 2>&1; then
    echo "✅ 服务启动成功！"
    echo "📱 访问地址: http://localhost:8000"
    echo "📖 API文档: http://localhost:8000/docs"
    echo "🛑 停止服务: ./stop.sh"
    echo "🔄 PID: $SERVER_PID"
    echo $SERVER_PID > .server.pid
else
    echo "❌ 服务启动失败"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi