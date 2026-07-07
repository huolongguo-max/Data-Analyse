#!/bin/bash
# ============================================================
# 打包脚本（macOS / Linux）
# 产出: dist/data-analysis-<版本>.tar.gz
#
# 打包前提条件：
#   1. frontend 已执行 npm run build
#   2. backend 已有 .venv 并安装了依赖
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
DIST="$ROOT/dist"
VERSION="1.0.0"
PKG_NAME="data-analysis-$VERSION"
PKG_DIR="$DIST/$PKG_NAME"

echo "============================================================"
echo " 打包 data-analysis v$VERSION"
echo "============================================================"
echo ""

# 清理旧产物
rm -rf "$PKG_DIR"
rm -f "$DIST/$PKG_NAME.tar.gz"
mkdir -p "$DIST" "$PKG_DIR"

# 检查前端构建产物
if [ ! -f "$ROOT/frontend/dist/index.html" ] && [ ! -f "$ROOT/backend/app/static/index.html" ]; then
    echo "[错误] 未找到前端构建产物。"
    echo "请先执行: cd frontend && npm run build"
    exit 1
fi

echo "[1/6] 创建目录结构..."
mkdir -p "$PKG_DIR/backend"
mkdir -p "$PKG_DIR/frontend"
mkdir -p "$PKG_DIR/data/uploads"
mkdir -p "$PKG_DIR/data/exports"
mkdir -p "$PKG_DIR/data/backups"
mkdir -p "$PKG_DIR/data/logs"
mkdir -p "$PKG_DIR/deploy"

echo "[2/6] 复制后端代码..."
rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='*.db' \
    "$ROOT/backend/app/" "$PKG_DIR/backend/app/"
rsync -a --exclude='__pycache__' \
    "$ROOT/backend/alembic/" "$PKG_DIR/backend/alembic/"
cp "$ROOT/backend/alembic.ini" "$PKG_DIR/backend/"
cp "$ROOT/backend/requirements.txt" "$PKG_DIR/backend/"
cp "$ROOT/backend/pyproject.toml" "$PKG_DIR/backend/"

echo "[3/6] 复制前端静态文件..."
# 如果 frontend/dist 存在，复制 dist
if [ -d "$ROOT/frontend/dist" ]; then
    cp -R "$ROOT/frontend/dist/"* "$PKG_DIR/backend/app/static/"
fi
# 复制 package.json 供参考
cp "$ROOT/frontend/package.json" "$PKG_DIR/frontend/"

echo "[4/6] 复制后端虚拟环境..."
# 仅复制 requirements.txt，目标机器自行安装
cp "$ROOT/backend/requirements.txt" "$PKG_DIR/"

echo "[5/6] 复制部署脚本和配置..."
cp "$ROOT/deploy/start.sh" "$PKG_DIR/deploy/"
cp "$ROOT/deploy/stop.sh" "$PKG_DIR/deploy/"
cp "$ROOT/deploy/backup_db.sh" "$PKG_DIR/deploy/"
cp "$ROOT/deploy/restore_db.sh" "$PKG_DIR/deploy/"
cp "$ROOT/deploy/production.env.example" "$PKG_DIR/deploy/"
cp "$ROOT/deploy/nginx.conf" "$PKG_DIR/deploy/"
cp "$ROOT/backend/start-backend.sh" "$PKG_DIR/"
cp "$ROOT/stop-backend.sh" "$PKG_DIR/"
cp "$ROOT/README.md" "$PKG_DIR/"
chmod +x "$PKG_DIR/deploy/"*.sh "$PKG_DIR/"*.sh

echo "[6/6] 生成部署说明..."
cat > "$PKG_DIR/部署说明.txt" << 'EOF'
# 部署步骤（macOS / Linux）

## 环境要求
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+（可选，开发环境可用 SQLite）

## 部署步骤

1. 将整个文件夹复制到目标机器任意位置
2. 将 deploy/production.env.example 复制为根目录的 .env
3. 编辑 .env，至少修改 POSTGRES_PASSWORD 和 SECRET_KEY
   生成 SECRET_KEY：
   python3 -c "import secrets; print(secrets.token_hex(32))"

4. 创建虚拟环境并安装依赖：
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

5. 启动服务：
   ./start-backend.sh

6. 浏览器访问 http://localhost:8000

## 管理命令
- 停止服务: ./stop-backend.sh
- 备份数据库: deploy/backup_db.sh
- 恢复数据库: deploy/restore_db.sh <备份文件>
EOF

# 打包
echo ""
echo "正在打包..."
cd "$DIST"
tar -czf "$PKG_NAME.tar.gz" "$PKG_NAME"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo " 打包完成: dist/$PKG_NAME.tar.gz"
    echo "============================================================"
else
    echo "[错误] 打包失败。"
    exit 1
fi
