# 本地储备表处理与看板系统

这个仓库当前包含两部分能力：

- `reserve_processor/`
  负责单个 `xlsx` 的补全计算与原样式导出。
- `backend/ + frontend/`
  负责批次上传、文件落盘、补全结果入库、看板查询和前端展示。

当前前端技术栈为 `Vue 3 + Vite`，构建产物会输出到 `backend/app/static/`，由 FastAPI 直接托管。

## 目录结构

```text
Data-Analyse/
├─ backend/                   FastAPI 后端
│  ├─ alembic/                数据库迁移
│  ├─ app/                    应用代码
│  └─ tests/                  后端测试
├─ frontend/                  Vue 3 前端源码
├─ reserve_processor/         单文件补全逻辑
├─ data/                      本地文件存储目录
│  ├─ uploads/                原始上传文件
│  ├─ exports/                补全后导出文件
│  ├─ backups/                备份
│  └─ logs/                   日志
├─ deploy/                    部署脚本（含 macOS .sh 和 Windows .bat）
├─ docs/                      需求文档与设计资料
├─ databoard-test.html        前端参考稿
└─ 储备表APP搭建V2.md          当前主需求文档
```
│  ├─ alembic/                数据库迁移
│  ├─ app/                    应用代码
│  └─ tests/                  后端测试
├─ frontend/                  Vue 3 前端源码
├─ reserve_processor/         单文件补全逻辑
├─ data/                      本地文件存储目录
│  ├─ uploads/                原始上传文件
│  ├─ exports/                补全后导出文件
│  ├─ backups/                备份
│  └─ logs/                   日志
├─ deploy/                    部署脚本
├─ docs/                      需求文档与设计资料
├─ databoard-test.html        前端参考稿
└─ 储备表APP搭建V2.md          当前主需求文档
```

## 当前能力

- 上传原始 `xlsx` 工作簿
- 调用 `reserve_processor` 生成补全后的三张业务表
- 原始工作簿落本地固定目录保存
- 补全工作簿落本地固定目录保存
- 补全后的结构化数据写入 SQL
- 前端支持：
  - 批次上传
  - 本期看板
  - 两期对比看板
  - 补全工作簿下载

## 数据口径

- 原始 `xlsx` 文件保存到 `data/uploads/`
- 补全后的 `xlsx` 文件保存到 `data/exports/`
- 补全后的结构化数据写入 PostgreSQL
- 文件元数据写入 `meta.uploaded_files`
- 前端所有看板只读查询最终补全后的数据，不在前端修改业务数据

V2 文档要求的看板数据来源已经对齐：

- 全国 / 片区 / 省份 / BD 看板：使用《已进线表》最终输出
- 课线 / 班期看板：使用《每月班期表》最终输出
- 城市 / 城市分课线看板：使用《储备明细表》最终输出

## 环境要求

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+（开发环境可选，SQLite 自动建表）

说明：

- 后端测试默认走 SQLite，不依赖本机 PostgreSQL
- 正式运行仍需 PostgreSQL
- 开发环境默认使用 SQLite（`DATABASE_URL=sqlite:///data/local-dev.db`），首次启动自动创建表

## 后端启动

### macOS / Linux

1. 复制环境变量模板

```bash
cp .env.example .env
```

2. 配置数据库和目录

至少确认这些变量（`.env` 文件中）：

- `DATABASE_URL`
- `UPLOAD_DIR`
- `EXPORT_DIR`
- `BACKUP_DIR`
- `LOG_DIR`
- `CORS_ORIGINS`

3. 安装依赖

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. 启动后端

```bash
# 方式一：直接启动
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 方式二：使用启动脚本
./backend/start-backend.sh
```

启动后：

- API 文档：`http://127.0.0.1:8000/api/docs`
- 前端页面：`http://127.0.0.1:8000/`

### Windows

1. 复制环境变量模板

```powershell
Copy-Item .env.example .env
```

2. 安装依赖

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. 启动后端

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 前端开发

前端源码在 `frontend/`，开发时走 Vite，API 请求代理到本地 FastAPI。

### macOS / Linux

```bash
cd frontend
npm install
npm run dev

# 或使用启动脚本
./frontend/start-frontend.sh
```

### Windows

```powershell
cd frontend
npm install
npm run dev
```

默认开发地址：

- 前端开发服务：`http://127.0.0.1:5173`
- 后端 API：`http://127.0.0.1:8000`

## 前端构建

```powershell
cd frontend
npm install
npm run build
```

构建产物会写到：

- `backend/app/static/index.html`
- `backend/app/static/assets/*`

FastAPI 会把它们作为正式页面静态资源托管。

## 测试

后端测试：

```powershell
cd backend
python -m pytest tests
```

本仓库目前没有单独前端测试框架；前端以 `npm run build` 作为基础编译校验。

## 主要接口

- `GET /api/health`
- `GET /api/version`
- `POST /api/imports/workbook`
- `POST /api/uploads/monthly-batch`
- `GET /api/imports/periods`
- `GET /api/periods`
- `GET /api/imports/periods/{period_code}/uploads`
- `GET /api/periods/{period_code}/uploads`
- `GET /api/dashboard/single`
- `GET /api/dashboard/compare`
- `GET /api/exports/completed-workbook`
- `GET /api/exports/completed-table`

## 文档位置

- 主需求文档：`储备表APP搭建V2.md`
- 归档需求文档：`docs/储备表APP搭建V2.md`
- 数据库规范：`docs/数据库规范.md`
- 数据处理维护说明：`reserve_processor/README.md`

## 当前已验证项

- `frontend` 已完成 Vue 3 重构并成功构建
- FastAPI 首页静态托管链路已打通
- 后端测试：`36 passed`

当前仍需依赖真实部署环境补齐的一项是：

- 正式 PostgreSQL 连接信息与驱动安装
