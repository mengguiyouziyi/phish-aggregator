#!/bin/bash

# 一键停止脚本
echo "🛑 停止 Phish Aggregator..."

# 从PID文件读取
if [ -f ".server.pid" ]; then
    PID=$(cat .server.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "🔧 停止进程 (PID: $PID)..."
        kill $PID
        sleep 2

        # 如果进程还在运行，强制杀死
        if kill -0 $PID 2>/dev/null; then
            echo "⚠️  强制停止进程..."
            kill -9 $PID
        fi

        echo "✅ 进程已停止"
    else
        echo "⚠️  进程不存在"
    fi
    rm -f .server.pid
else
    # 通过进程名查找
    echo "🔍 查找运行中的进程..."
    PIDS=$(pgrep -f "uvicorn.*8000")
    if [ -n "$PIDS" ]; then
        echo "🔧 停止进程: $PIDS"
        pkill -f "uvicorn.*8000"
        sleep 2

        # 检查是否还有残留进程
        REMAINING=$(pgrep -f "uvicorn.*8000")
        if [ -n "$REMAINING" ]; then
            echo "⚠️  强制停止残留进程..."
            pkill -9 -f "uvicorn.*8000"
        fi

        echo "✅ 所有进程已停止"
    else
        echo "⚠️  没有找到运行中的进程"
    fi
fi

# 检查端口是否还在占用
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口8000仍被占用，可能需要手动处理"
    lsof -Pi :8000
else
    echo "✅ 端口8000已释放"
fi