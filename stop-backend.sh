#!/bin/bash
# 停止后端服务（macOS / Linux）
# 用法: ./stop-backend.sh [端口号]  默认端口 8000

PORT="${1:-8000}"

echo "停止监听端口 $PORT 的服务..."

# 查找占用指定端口的进程并终止
PIDS=$(lsof -ti :"$PORT" 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo "端口 $PORT 上没有运行中的服务。"
else
    echo "$PIDS" | while read pid; do
        kill "$pid" 2>/dev/null && echo "  已终止 PID $pid"
    done
    # 如果首次未成功，强制终止
    sleep 1
    REMAINING=$(lsof -ti :"$PORT" 2>/dev/null)
    if [ -n "$REMAINING" ]; then
        echo "$REMAINING" | while read pid; do
            kill -9 "$pid" 2>/dev/null && echo "  已强制终止 PID $pid"
        done
    fi
    echo "完成。"
fi
