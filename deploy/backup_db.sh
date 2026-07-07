#!/bin/bash
# ============================================================
# 数据库备份脚本（macOS / Linux）
# 用法: ./backup_db.sh
# 备份文件: data/backups/db_backup_<时间戳>.sql
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
DATA="$ROOT/data"
ENV_FILE="$ROOT/.env"
BACKUP_DIR="$DATA/backups"

# 生成时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# 确保备份目录存在
mkdir -p "$BACKUP_DIR"

# 读取配置
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

DB_NAME="${POSTGRES_DB:-reserve_app}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"

echo "正在备份数据库 $DB_NAME ..."

if command -v pg_dump &> /dev/null; then
    pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f "$BACKUP_FILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "备份成功: $BACKUP_FILE"
    else
        echo "[错误] 备份失败！请确认数据库正在运行。"
        exit 1
    fi
elif [ -f "$DATA/local-dev.db" ]; then
    # SQLite 备份
    echo "[提示] 检测到 SQLite 数据库，使用文件复制方式备份..."
    cp "$DATA/local-dev.db" "$BACKUP_DIR/local-dev_$TIMESTAMP.db"
    echo "备份成功: $BACKUP_DIR/local-dev_$TIMESTAMP.db"
else
    echo "[错误] 未找到 pg_dump 或 SQLite 数据库文件。"
    exit 1
fi
