@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set ROOT=%~dp0..
set PGSQL=%ROOT%\pgsql
set FRONTEND=%ROOT%\frontend

echo ============================================================
echo  本地数据分析工具 - 停止
echo ============================================================
echo.

:: 停止 Nginx
echo [1/2] 停止前端服务（Nginx）...
taskkill /f /im nginx.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo     Nginx 已停止。
) else (
    echo     Nginx 未在运行。
)

:: 停止后端
echo [2/3] 停止后端服务...
taskkill /f /fi "WINDOWTITLE eq local_backend" >nul 2>&1
:: 兜底：按端口找进程
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo     后端服务已停止。

:: 停止 PostgreSQL
echo [3/3] 停止 PostgreSQL...
"%PGSQL%\bin\pg_ctl.exe" stop -D "%PGSQL%\data" -m fast >nul 2>&1
if %errorlevel% equ 0 (
    echo     PostgreSQL 已停止。
) else (
    echo     PostgreSQL 未在运行。
)

echo.
echo 所有服务已停止。
pause
