@echo off
REM 启动���端服务器的批处理脚本
REM 使用优化的 uvicorn 配置避免重载卡死问题

cd /d "%~dp0"

REM 设置邮箱密码环境变量
set EMAIL_PASSWORD=xajhzindwfrwbgde

REM 启动服务器（不使用 --reload 模式以避免 Windows 上的卡死问题）
echo Starting backend server...
echo Server will run on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

"%~dp0venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
