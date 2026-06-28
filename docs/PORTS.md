# 端口与前端组件映射文档

## 一、端口规划

### 1.1 开发环境（本机）

| 服务 | 地址 | 端口 | 说明 |
|------|------|------|------|
| 前端开发服务器 | `http://localhost:5173` | 5173 | Vite dev server，`npm run dev` 启动 |
| 后端 API 服务 | `http://127.0.0.1:8000` | 8000 | FastAPI，`uvicorn app.main:app --reload` 启动 |
| PostgreSQL 数据库 | `localhost:5432` | 5432 | 本地安装的 PostgreSQL |
| FastAPI 文档 | `http://127.0.0.1:8000/api/docs` | 8000 | Swagger UI，仅开发环境可用 |

> 开发时前端通过 Vite 代理将 `/api/*` 转发到 `http://127.0.0.1:8000`，无需额外配置。

---

### 1.2 目标机部署环境

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx（前端入口） | **80** | 对外唯一端口，托管前端静态文件 + 反代后端 |
| FastAPI 后端 | 8000 | 监听 `127.0.0.1`，仅 Nginx 可达 |
| PostgreSQL 数据库 | 5432 | 监听 `localhost`，仅后端可达 |

> 部署采用 Windows 原生运行，不使用 Docker。  
> 所有服务均运行在目标机本地，对外仅暴露端口 80。  
> 访问地址：`http://<目标机IP>` 或 `http://localhost`

---

### 1.3 部署方式

| 项目 | 值 |
|------|----|
| 部署方式 | 打包为 zip，解压即用 |
| 运行时依赖 | 全部内嵌（Python embeddable + PostgreSQL portable + Nginx for Windows） |
| 对外端口 | 80（HTTP） |
| 数据持久化 | `data/` 目录（uploads、exports、backups、logs） |
| 数据库持久化 | `pgsql/data/` 目录 |

如需修改对外端口（如改为 8080），编辑 `frontend/conf/default.conf`：
```nginx
listen 8080;
```

---

## 二、部署包目录结构

```
local-data-analysis-<版本>/
├── 一键启动.bat            # 快捷启动入口
├── 一键停止.bat            # 快捷停止入口
├── .env                    # 环境变量（从模板复制后手动修改）
├── 部署说明.txt
├── PORTS.md
├── README.md
├── backend/                # FastAPI 后端代码
│   ├── app/
│   ├── alembic/
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/               # Nginx + 前端静态文件
│   ├── nginx.exe
│   ├── conf/default.conf   # Nginx 配置
│   └── html/               # Vue 构建产物
├── python/                 # Python 3.12 embeddable + pip 依赖
├── pgsql/                  # PostgreSQL portable
│   ├── bin/
│   └── data/               # 数据库数据（首次启动时初始化）
├── data/                   # 用户数据
│   ├── uploads/
│   ├── exports/
│   ├── backups/
│   └── logs/
└── deploy/                 # 管理脚本
    ├── start.bat
    ├── stop.bat
    ├── backup_db.bat
    ├── restore_db.bat
    └── production.env.example
```

---

## 三、前端组件结构

### 3.1 页面视图（Views）

| 路由路径 | 文件 | 说明 |
|---------|------|------|
| `/login` | `views/auth/LoginView.vue` | 登录页 |
| `/admin` / `/admin/home` | `views/admin/HomeView.vue` | 管理首页 / 数据概览 |
| `/admin/upload` | `views/admin/UploadImportView.vue` | 文件上传与导入向导 |
| `/admin/imports` | `views/admin/ImportHistoryView.vue` | 导入历史列表 |
| `/admin/imports/:id` | `views/admin/ImportDetailView.vue` | 导入批次详情 |
| `/admin/data` | `views/admin/DataManageView.vue` | 数据集管理 |
| `/admin/dashboard` | `views/admin/DashboardView.vue` | 数据看板 |
| `/admin/analysis` | `views/admin/AnalysisView.vue` | 自定义分析 |
| `/admin/templates` | `views/admin/TemplateManageView.vue` | 字段模板管理 |
| `/admin/users` | `views/admin/UserManageView.vue` | 用户管理（仅管理员） |
| `/admin/settings` | `views/admin/SystemSettingView.vue` | 系统设置 |
| `*` | `views/error/NotFoundView.vue` | 404 页面 |

---

### 3.2 布局组件（Layouts）

| 文件 | 用途 |
|------|------|
| `layouts/AuthLayout.vue` | 登录页布局（居中卡片，无侧边栏） |
| `layouts/AdminLayout.vue` | 后台管理布局（含顶栏 + 侧边栏 + 内容区） |

---

### 3.3 全局通用组件（components/global/）

| 组件文件 | 用途 |
|---------|------|
| `AppHeader.vue` | 顶部导航栏（Logo、用户信息、退出） |
| `AppSidebar.vue` | 左侧菜单栏（路由导航） |
| `AppBreadcrumb.vue` | 面包屑导航 |
| `PageContainer.vue` | 页面内容区容器（统一 padding/标题） |
| `FileUploader.vue` | 文件拖拽上传组件（封装 el-upload） |
| `DataTable.vue` | 通用数据表格（分页、排序、列配置） |
| `EmptyState.vue` | 空状态占位图 |
| `ConfirmDialog.vue` | 二次确认对话框 |
| `ChartCard.vue` | 图表卡片容器（标题 + ECharts 实例） |

---

### 3.4 导入流程组件（components/import/）

| 组件文件 | 用途 |
|---------|------|
| `UploadStep.vue` | 第1步：文件上传 |
| `SheetSelectStep.vue` | 第2步：选择 Sheet |
| `PreviewTable.vue` | 第3步：数据预览表格 |
| `FieldMappingPanel.vue` | 第4步：字段映射配置 |
| `ValidationResult.vue` | 第5步：校验结果展示 |
| `ImportResultPanel.vue` | 第6步：导入完成结果 |

---

### 3.5 看板组件（components/dashboard/）

| 组件文件 | 用途 |
|---------|------|
| `SummaryCards.vue` | 顶部数据汇总卡片（总数、金额等） |
| `TrendChart.vue` | 趋势折线图 / 柱状图 |
| `DistributionChart.vue` | 分布饼图 / 环图 |
| `RankingChart.vue` | 排名条形图 |
| `DashboardFilter.vue` | 看板筛选器（时间范围、维度选择） |

---

### 3.6 分析组件（components/analysis/）

| 组件文件 | 用途 |
|---------|------|
| `DatasetSelector.vue` | 数据集选择器 |
| `FieldSelector.vue` | 分析字段选择（维度 / 度量） |
| `FilterBuilder.vue` | 动态筛选条件构建器 |
| `AnalysisResultTable.vue` | 分析结果表格 |
| `ChartTypeSelector.vue` | 图表类型切换（柱/折/饼/散点） |

---

## 四、前端 API 模块与后端路由对应

| API 文件 | 对应后端路由前缀 | 主要功能 |
|---------|---------------|---------|
| `api/auth.ts` | `/api/auth` | 登录、刷新 token、登出 |
| `api/users.ts` | `/api/users` | 用户 CRUD |
| `api/files.ts` | `/api/files` | 文件上传、预览、删除 |
| `api/imports.ts` | `/api/imports` | 导入任务管理 |
| `api/templates.ts` | `/api/templates` | 字段模板 CRUD |
| `api/datasets.ts` | `/api/datasets` | 数据集查询 |
| `api/dashboard.ts` | `/api/dashboard` | 看板数据聚合 |
| `api/analysis.ts` | `/api/analysis` | 自定义分析查询 |
| `api/exports.ts` | `/api/exports` | 数据导出 |
| `api/system.ts` | `/api/system` | 系统配置、操作日志 |

---

## 五、关键配置文件速查

| 需要修改的内容 | 配置文件 |
|-------------|---------|
| 对外端口 | `frontend/conf/default.conf` → `listen` |
| 数据库账号密码 | `.env`（生产）/ `.env.example`（开发） |
| JWT 密钥 | `.env` → `SECRET_KEY` |
| 文件存储路径 | `.env` → `UPLOAD_DIR` 等 |
| Nginx 反代 / 上传限制 | `frontend/conf/default.conf` 或 `deploy/nginx.conf`（源码） |
| 前端开发代理 | `frontend/local-data-ui/vite.config.ts` |
| 后端 CORS 允许源 | `backend/app/main.py` |
| 打包版本号 | `build_release.bat` → `VERSION` 变量 |
