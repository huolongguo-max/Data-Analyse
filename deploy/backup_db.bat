@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set ROOT=%~dp0..
set PGSQL=%ROOT%\pgsql
set DATA=%ROOT%\data
set ENV_FILE=%ROOT%\.env
set BACKUP_DIR=%DATA%\backups

:: 生成时间戳
for /f "tokens=1-3 delims=/" %%a in ("%date%") do set D=%%a%%b%%c
for /f "tokens=1-3 delims=:." %%a in ("%time: =0%") do set T=%%a%%b%%c
set TIMESTAMP=%D%_%T%
set BACKUP_FILE=%BACKUP_DIR%\db_backup_%TIMESTAMP%.sql

:: 读取配置
for /f "tokens=1,* delims==" %%a in ('type "%ENV_FILE%" ^| findstr /i "POSTGRES_DB"') do set PG_DB=%%b
for /f "tokens=1,* delims==" %%a in ('type "%ENV_FILE%" ^| findstr /i "POSTGRES_PASSWORD"') do set PGPASSWORD=%%b

echo 正在备份数据库 !PG_DB! ...
"%PGSQL%\bin\pg_dump.exe" -U postgres -d "!PG_DB!" -f "%BACKUP_FILE%"

if %errorlevel% equ 0 (
    echo 备份成功：%BACKUP_FILE%
) else (
    echo [错误] 备份失败！请确认数据库正在运行。
)

pause
