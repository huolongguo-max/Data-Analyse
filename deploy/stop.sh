#!/bin/bash
# ============================================================
# 本地数据分析工具 - 停止脚本（macOS / Linux）
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
DATA="$ROOT/data"

echo "============================================================"
echo " 本地数据分析工具 - 停止"
echo "============================================================"
echo ""

# 停止后端（端口 8000）
echo "[1/2] 停止后端服务..."
PIDS=$(lsof -ti :8000 2>/dev/null)
if [ -n "$PIDS" ]; then
    echo "$PIDS" | while read pid; do
        kill "$pid" 2>/dev/null && echo "     已终止后端进程 PID $pid"
    done
    sleep 1
    # 强制终止残留
    REMAIN=$(lsof -ti :8000 2>/dev/null)
    if [ -n "$REMAIN" ]; then
        echo "$REMAIN" | while read pid; do
            kill -9 "$pid" 2>/dev/null
        done
    fi
else
    echo "     后端服务未在运行。"
fi

# 停止 Nginx
echo "[2/2] 停止前端服务（Nginx）..."
if command -v nginx &> /dev/null; then
    nginx -s quit 2>/dev/null && echo "     Nginx 已停止。" || echo "     Nginx 未在运行。"
else
    echo "     [跳过] 未安装 Nginx。"
fi

echo ""
echo "所有服务已停止。"
