#!/bin/bash
# 后台启动 FastAPI 后端服务（macOS / Linux）
# 用法: ./start-backend-daemon.sh
# 服务将在后台运行，日志输出到 data/logs/backend.log

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
LOG_DIR="$SCRIPT_DIR/data/logs"
PORT="${1:-8000}"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

if [ ! -d "$BACKEND_DIR/.venv" ]; then
    echo "[错误] 未找到 $BACKEND_DIR/.venv 虚拟环境"
    exit 1
fi

echo "后台启动后端服务（端口 $PORT）..."
cd "$BACKEND_DIR"
source .venv/bin/activate

nohup python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" \
    >> "$LOG_DIR/backend.log" 2>&1 &

PID=$!
echo "后端服务已启动（PID: $PID）"
echo "日志文件: $LOG_DIR/backend.log"
echo "停止服务: ./stop-backend.sh $PORT"
