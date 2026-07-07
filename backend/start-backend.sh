#!/bin/bash
# 启动 FastAPI 后端服务（macOS / Linux）
# 用法: ./start-backend.sh [端口号]  默认端口 8000

cd "$(dirname "$0")"
PORT="${1:-8000}"

if [ ! -d ".venv" ]; then
    echo "[错误] 未找到 .venv 虚拟环境，请先运行："
    echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "启动后端服务（端口 $PORT）..."
source .venv/bin/activate
exec python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --app-dir .
