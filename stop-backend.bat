@echo off
chcp 65001 >nul
echo Stopping backend service...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
    taskkill /F /PID %%p 2>nul
)
echo Done.
