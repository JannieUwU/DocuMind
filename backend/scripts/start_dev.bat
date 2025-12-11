@echo off
REM 开发模式启动脚本 - 带热重载功能
REM 使用 watchfiles 重载器替代默认的 WatchFiles，更稳定

cd /d "%~dp0"

REM 设置邮箱密码环境变量
set EMAIL_PASSWORD=xajhzindwfrwbgde

REM 启动开发服务器（使用 --reload-dir 限制监控范围，避免卡死）
echo Starting backend server in DEVELOPMENT mode...
echo Hot reload is ENABLED (only watching main.py and current directory)
echo Server will run on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
echo If the server hangs during reload:
echo 1. Press Ctrl+C to stop
echo 2. Run this script again
echo.

"%~dp0venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir . --reload-exclude "venv/*" --reload-exclude "__pycache__/*"

pause
