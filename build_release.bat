@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================
:: 打包脚本（在开发机上运行）
:: 产出：dist\local-data-analysis-<版本>.zip
::
:: 打包前提条件（开发机需准备好）：
::   1. frontend/local-data-ui 已执行 npm run build
::   2. 已下载：
::      - Python embeddable: https://www.python.org/ftp/python/3.12.x/python-3.12.x-embed-amd64.zip
::        解压到 tools\python\
::      - PostgreSQL portable: https://www.enterprisedb.com/download-postgresql-binaries
::        解压 binaries 到 tools\pgsql\
::      - Nginx for Windows: http://nginx.org/en/download.html
::        解压到 tools\nginx\
::   3. 已在 tools\python\ 中用 get-pip.py 安装依赖：
::      python.exe -m pip install -r backend\requirements.txt
:: ============================================================

set ROOT=%~dp0
set DIST=%ROOT%dist
set VERSION=1.0.0
set PKG_NAME=local-data-analysis-%VERSION%
set PKG_DIR=%DIST%\%PKG_NAME%
set TOOLS=%ROOT%tools

echo ============================================================
echo  打包 local-data-analysis v%VERSION%
echo ============================================================
echo.

:: 清理旧产物
if exist "%PKG_DIR%" rmdir /s /q "%PKG_DIR%"
if exist "%DIST%\%PKG_NAME%.zip" del "%DIST%\%PKG_NAME%.zip"
if not exist "%DIST%" mkdir "%DIST%"

:: ── 检查前端构建产物 ──────────────────────────────────────────
if not exist "%ROOT%frontend\local-data-ui\dist\index.html" (
    echo [错误] 未找到前端构建产物。
    echo 请先执行：cd frontend\local-data-ui ^&^& npm run build
    pause
    exit /b 1
)

:: ── 检查 tools\ 目录 ──────────────────────────────────────────
for %%d in (python pgsql nginx) do (
    if not exist "%TOOLS%\%%d\" (
        echo [错误] 未找到 tools\%%d\
        echo 请参考脚本顶部注释准备 tools\ 目录。
        pause
        exit /b 1
    )
)

echo [1/6] 创建目录结构...
mkdir "%PKG_DIR%\backend"
mkdir "%PKG_DIR%\frontend"
mkdir "%PKG_DIR%\data\uploads"
mkdir "%PKG_DIR%\data\exports"
mkdir "%PKG_DIR%\data\backups"
mkdir "%PKG_DIR%\data\logs"
mkdir "%PKG_DIR%\deploy"
mkdir "%PKG_DIR%\python"
mkdir "%PKG_DIR%\pgsql"

echo [2/6] 复制后端代码...
xcopy /e /i /q "%ROOT%backend\app" "%PKG_DIR%\backend\app\"
xcopy /e /i /q "%ROOT%backend\alembic" "%PKG_DIR%\backend\alembic\"
copy "%ROOT%backend\alembic.ini" "%PKG_DIR%\backend\"
copy "%ROOT%backend\requirements.txt" "%PKG_DIR%\backend\"
:: 不复制 node_modules、__pycache__、.env 等
for /d /r "%PKG_DIR%\backend" %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)

echo [3/6] 复制前端静态文件 + Nginx...
xcopy /e /i /q "%TOOLS%\nginx" "%PKG_DIR%\frontend\"
:: 覆盖 nginx 默认 conf 和 html
copy "%ROOT%deploy\nginx.conf" "%PKG_DIR%\frontend\conf\default.conf"
xcopy /e /i /q "%ROOT%frontend\local-data-ui\dist" "%PKG_DIR%\frontend\html\"

echo [4/6] 复制 Python embeddable + 依赖...
xcopy /e /i /q "%TOOLS%\python" "%PKG_DIR%\python\"

echo [5/6] 复制 PostgreSQL portable...
xcopy /e /i /q "%TOOLS%\pgsql" "%PKG_DIR%\pgsql\"

echo [6/6] 复制部署脚本和配置模板...
copy "%ROOT%deploy\start.bat" "%PKG_DIR%\deploy\"
copy "%ROOT%deploy\stop.bat" "%PKG_DIR%\deploy\"
copy "%ROOT%deploy\backup_db.bat" "%PKG_DIR%\deploy\"
copy "%ROOT%deploy\restore_db.bat" "%PKG_DIR%\deploy\"
copy "%ROOT%deploy\production.env.example" "%PKG_DIR%\deploy\"
copy "%ROOT%PORTS.md" "%PKG_DIR%\"
copy "%ROOT%README.md" "%PKG_DIR%\"

:: 生成快捷启动脚本（放根目录，双击即可）
(
echo @echo off
echo cd /d "%%~dp0deploy"
echo call start.bat
) > "%PKG_DIR%\一键启动.bat"

(
echo @echo off
echo cd /d "%%~dp0deploy"
echo call stop.bat
) > "%PKG_DIR%\一键停止.bat"

:: 生成部署说明
(
echo # 部署步骤
echo.
echo 1. 将整个文件夹复制到目标机器任意位置（路径不要有中文或空格）
echo 2. 将 deploy\production.env.example 复制为根目录的 .env
echo 3. 编辑 .env，至少修改 POSTGRES_PASSWORD 和 SECRET_KEY
echo    生成 SECRET_KEY：在 python 目录下运行：
echo    python.exe -c "import secrets; print(secrets.token_hex(32))"
echo 4. 双击"一键启动.bat"
echo 5. 浏览器访问 http://localhost
echo.
echo 后续管理：
echo - 停止服务：双击"一键停止.bat"
echo - 备份数据库：deploy\backup_db.bat
echo - 恢复数据库：deploy\restore_db.bat ^<备份文件^>
) > "%PKG_DIR%\部署说明.txt"

:: ── 打 zip ────────────────────────────────────────────────────
echo.
echo 正在压缩...
powershell -NoProfile -Command "Compress-Archive -Path '%PKG_DIR%' -DestinationPath '%DIST%\%PKG_NAME%.zip' -Force"

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo  打包完成：dist\%PKG_NAME%.zip
    echo ============================================================
) else (
    echo [错误] 压缩失败。
)

pause
