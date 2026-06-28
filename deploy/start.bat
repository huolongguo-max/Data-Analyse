@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================
:: 本地数据分析工具 - 启动脚本
:: 适用于解压后的部署包（Windows 原生，无 Docker）
:: 目录结构：
::   app\
::     backend\        FastAPI 后端
::     frontend\       Nginx + 前端静态文件
::     data\           数据目录
::     pgsql\          PostgreSQL portable
::     python\         Python embeddable
::     deploy\         本脚本所在目录
::     .env            环境变量（从 production.env.example 复制）
:: ============================================================

set ROOT=%~dp0..
set PGSQL=%ROOT%\pgsql
set PYTHON=%ROOT%\python
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend
set DATA=%ROOT%\data
set ENV_FILE=%ROOT%\.env

echo ============================================================
echo  本地数据分析工具 - 启动
echo ============================================================
echo.

:: 检查 .env
if not exist "%ENV_FILE%" (
    echo [错误] 未找到 .env 文件。
    echo 请将 deploy\production.env.example 复制为根目录的 .env 并修改配置。
    pause
    exit /b 1
)

:: 创建数据目录
for %%d in (uploads exports backups logs) do (
    if not exist "%DATA%\%%d" mkdir "%DATA%\%%d"
)

:: ── 1. 启动 PostgreSQL ────────────────────────────────────────
echo [1/3] 启动 PostgreSQL...
set PG_DATA=%PGSQL%\data
set PG_BIN=%PGSQL%\bin

if not exist "%PG_DATA%\PG_VERSION" (
    echo     首次运行，初始化数据库...
    :: 从 .env 读取密码
    for /f "tokens=1,* delims==" %%a in ('type "%ENV_FILE%" ^| findstr /i "POSTGRES_PASSWORD"') do (
        set PG_PASS=%%b
    )
    echo !PG_PASS! > "%PGSQL%\pwfile.tmp"
    "%PG_BIN%\initdb.exe" -D "%PG_DATA%" -U postgres --pwfile="%PGSQL%\pwfile.tmp" -E UTF8 --locale=C
    del "%PGSQL%\pwfile.tmp"
)

:: 检查是否已在运行
"%PG_BIN%\pg_ctl.exe" status -D "%PG_DATA%" >nul 2>&1
if %errorlevel% neq 0 (
    "%PG_BIN%\pg_ctl.exe" start -D "%PG_DATA%" -l "%DATA%\logs\postgresql.log" -w
    if !errorlevel! neq 0 (
        echo [错误] PostgreSQL 启动失败，请查看 data\logs\postgresql.log
        pause
        exit /b 1
    )
)
echo     PostgreSQL 已运行。

:: 创建数据库（如不存在）
for /f "tokens=1,* delims==" %%a in ('type "%ENV_FILE%" ^| findstr /i "POSTGRES_DB"') do set PG_DB=%%b
for /f "tokens=1,* delims==" %%a in ('type "%ENV_FILE%" ^| findstr /i "POSTGRES_PASSWORD"') do set PG_PASS=%%b
set PGPASSWORD=!PG_PASS!
"%PG_BIN%\psql.exe" -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='!PG_DB!'" | findstr /c:"1" >nul 2>&1
if %errorlevel% neq 0 (
    echo     创建数据库 !PG_DB!...
    "%PG_BIN%\psql.exe" -U postgres -c "CREATE DATABASE \"!PG_DB!\" ENCODING 'UTF8';"
)

:: ── 2. 启动后端 ───────────────────────────────────────────────
echo [2/3] 启动后端服务...
cd /d "%BACKEND%"
set PYTHONPATH=%BACKEND%

:: 运行 Alembic 迁移
echo     执行数据库迁移...
"%PYTHON%\python.exe" -m alembic upgrade head
if %errorlevel% neq 0 (
    echo [警告] 数据库迁移失败，请检查配置。
)

:: 后台启动 uvicorn
start "local_backend" /min "%PYTHON%\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
echo     后端服务已启动（端口 8000）。

:: 等待后端就绪
timeout /t 3 /nobreak >nul

:: ── 3. 启动 Nginx（前端） ─────────────────────────────────────
echo [3/3] 启动前端服务（Nginx）...
cd /d "%FRONTEND%"
start "local_frontend" /min nginx.exe
echo     前端服务已启动（端口 80）。

echo.
echo ============================================================
echo  启动完成！
echo  访问地址: http://localhost
echo  API 文档: http://localhost/api/docs
echo ============================================================
echo.
pause
