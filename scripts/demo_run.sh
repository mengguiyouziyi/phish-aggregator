#!/usr/bin/env bash
set -e
echo "[*] 创建虚拟环境并安装依赖 ..."
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
echo "[*] 拉取规则清单（容错） ..."
python scripts/fetch_rules.py || true
echo "[*] 启动服务 http://localhost:8000"
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
