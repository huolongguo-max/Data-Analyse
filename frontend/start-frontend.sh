#!/bin/bash
# 启动 Vite 前端开发服务器（macOS / Linux）
# 用法: ./start-frontend.sh [端口号]  默认端口 5173

cd "$(dirname "$0")"
PORT="${1:-5173}"

if [ ! -d "node_modules" ]; then
    echo "[错误] 未找到 node_modules，请先运行 npm install"
    exit 1
fi

echo "启动前端开发服务器（端口 $PORT）..."
npm run dev -- --host 0.0.0.0 --port "$PORT"
