@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set ROOT=%~dp0..
set PGSQL=%ROOT%\pgsql
set ENV_FILE=%ROOT%\.env

if "%1"=="" (
    echo 用法: restore_db.bat ^<备份文件路径^>
    echo 示例: restore_db.bat ..\data\backups\db_backup_20260601_120000.sql
    pause
    exit /b 1
)

set BACKUP_FILE=%1

if not exist "%BACKUP_FILE%" (
    echo [错误] 备份文件不存在：%BACKUP_FILE%
    pause
    exit /b 1
)

:: 读取配置
for /f "tokens=1,* delims==" %%a in ('type "%ENV_FILE%" ^| findstr /i "POSTGRES_DB"') do set PG_DB=%%b
for /f "tokens=1,* delims==" %%a in ('type "%ENV_FILE%" ^| findstr /i "POSTGRES_PASSWORD"') do set PGPASSWORD=%%b

echo 警告：此操作将覆盖数据库 !PG_DB! 的全部数据！
set /p CONFIRM=确认恢复？请输入 YES 继续：
if /i not "!CONFIRM!"=="YES" (
    echo 操作已取消。
    pause
    exit /b 0
)

echo 正在恢复数据库...
"%PGSQL%\bin\psql.exe" -U postgres -d "!PG_DB!" -f "%BACKUP_FILE%"

if %errorlevel% equ 0 (
    echo 恢复成功！
) else (
    echo [错误] 恢复失败！请检查备份文件格式和数据库状态。
)

pause
