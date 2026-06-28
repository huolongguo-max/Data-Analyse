@echo off
cd /d "%~dp0"
call ".venv312\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir .
