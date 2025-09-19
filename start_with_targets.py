#!/usr/bin/env python3
"""
启动脚本：初始化目标网站并启动服务器
"""

import asyncio
import subprocess
import sys
import os
import time

async def initialize_and_start():
    """初始化目标网站并启动服务器"""
    print("🚀 启动钓鱼检测系统...")

    # 1. 初始化目标网站
    print("\n🎯 初始化目标网站...")
    try:
        # 切换到后端目录
        backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
        os.chdir(backend_dir)

        # 初始化目标网站
        from app.services.visual_detector import initialize_targets
        await initialize_targets()

        print("✅ 目标网站初始化完成")
    except Exception as e:
        print(f"❌ 目标网站初始化失败: {e}")
        print("系统将继续启动，但视觉检测可能无法正常工作")

    # 2. 启动服务器
    print("\n🌐 启动API服务器...")
    try:
        # 启动uvicorn服务器
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        print("✅ 服务器启动成功")
        print("📍 API地址: http://localhost:8000")
        print("📖 API文档: http://localhost:8000/docs")
        print("🎯 前端界面: http://localhost:8000/")
        print("\n按 Ctrl+C 停止服务器")

        # 实时输出日志
        for line in iter(process.stdout.readline, ''):
            print(line.strip())

        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务器...")
        process.terminate()
        process.wait()
        print("✅ 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    asyncio.run(initialize_and_start())