#!/bin/bash
# ============================================================
# 本地数据分析工具 - 启动脚本（macOS / Linux）
# 适用于解压后的部署包
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
DATA="$ROOT/data"
ENV_FILE="$ROOT/.env"

echo "============================================================"
echo " 本地数据分析工具 - 启动"
echo "============================================================"
echo ""

# 检查 .env
if [ ! -f "$ENV_FILE" ]; then
    echo "[错误] 未找到 .env 文件。"
    echo "请将 deploy/production.env.example 复制为根目录的 .env 并修改配置。"
    exit 1
fi

# 创建数据目录
for d in uploads exports backups logs; do
    mkdir -p "$DATA/$d"
done

# 加载 .env
set -a
source "$ENV_FILE"
set +a

# ── 1. 启动 PostgreSQL ────────────────────────────────────────
echo "[1/3] 检查 PostgreSQL..."

# macOS 上通常使用 brew 安装的 PostgreSQL
if command -v pg_isready &> /dev/null; then
    if ! pg_isready -q 2>/dev/null; then
        echo "     启动 PostgreSQL..."
        pg_ctl start -D /usr/local/var/postgresql@16 -l "$DATA/logs/postgresql.log" -w 2>/dev/null || \
        pg_ctl start -D /opt/homebrew/var/postgresql@16 -l "$DATA/logs/postgresql.log" -w 2>/dev/null || \
        brew services start postgresql@16 2>/dev/null || \
        echo "     [警告] 无法自动启动 PostgreSQL，请手动启动"
    else
        echo "     PostgreSQL 已运行。"
    fi
else
    echo "     [提示] 未检测到 PostgreSQL，跳过（开发模式可使用 SQLite）"
fi

# 创建数据库（如不存在且连接到 PostgreSQL）
if command -v psql &> /dev/null && [ -n "${POSTGRES_DB:-}" ]; then
    DB_EXISTS=$(PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" psql -U "${POSTGRES_USER:-postgres}" -h "${POSTGRES_HOST:-localhost}" -tc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'" 2>/dev/null || echo "")
    if [ "$DB_EXISTS" != "1" ]; then
        echo "     创建数据库 ${POSTGRES_DB}..."
        PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" createdb -U "${POSTGRES_USER:-postgres}" -h "${POSTGRES_HOST:-localhost}" -E UTF8 "${POSTGRES_DB}" 2>/dev/null || true
    fi
fi

# ── 2. 启动后端 ───────────────────────────────────────────────
echo "[2/3] 启动后端服务..."
cd "$BACKEND"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 运行数据库迁移
echo "     执行数据库迁移..."
python -m alembic upgrade head 2>/dev/null || echo "     [警告] 数据库迁移失败，请检查配置。"

# 后台启动 uvicorn
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 \
    >> "$DATA/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo "     后端服务已启动（PID: $BACKEND_PID，端口 8000）。"

sleep 2

# ── 3. 启动 Nginx ─────────────────────────────────────────────
echo "[3/3] 启动前端服务（Nginx）..."
if command -v nginx &> /dev/null; then
    # 使用项目自带的 nginx.conf
    nginx -c "$ROOT/deploy/nginx.conf" -p "$FRONTEND" 2>/dev/null || \
    nginx 2>/dev/null || \
    echo "     [提示] Nginx 启动失败，可直接访问后端: http://localhost:8000"
    echo "     前端服务已启动（端口 80）。"
else
    echo "     [提示] 未安装 Nginx，可直接访问后端: http://localhost:8000"
    echo "     安装 Nginx: brew install nginx"
fi

echo ""
echo "============================================================"
echo " 启动完成！"
echo " 前端访问: http://localhost"
echo " API 文档: http://localhost:8000/api/docs"
echo "============================================================"
