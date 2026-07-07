#!/bin/bash
# ============================================================
# 数据库恢复脚本（macOS / Linux）
# 用法: ./restore_db.sh <备份文件路径>
# 示例: ./restore_db.sh ../data/backups/db_backup_20260601_120000.sql
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$ROOT/.env"

if [ -z "$1" ]; then
    echo "用法: restore_db.sh <备份文件路径>"
    echo "示例: restore_db.sh ../data/backups/db_backup_20260601_120000.sql"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "[错误] 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

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

echo "⚠️  警告: 此操作将覆盖数据库 $DB_NAME 的全部数据！"
read -r -p "确认恢复？请输入 YES 继续: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo "操作已取消。"
    exit 0
fi

# 检测备份文件类型并恢复
if [[ "$BACKUP_FILE" == *.sql ]]; then
    echo "正在恢复 PostgreSQL 数据库..."
    psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f "$BACKUP_FILE"
elif [[ "$BACKUP_FILE" == *.db ]]; then
    echo "正在恢复 SQLite 数据库..."
    DATA_DIR="$ROOT/data"
    cp "$BACKUP_FILE" "$DATA_DIR/local-dev.db"
    echo "恢复成功！"
    exit 0
else
    echo "[错误] 无法识别的备份文件格式: $BACKUP_FILE"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo "恢复成功！"
else
    echo "[错误] 恢复失败！请检查备份文件格式和数据库状态。"
    exit 1
fi
