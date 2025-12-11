@echo off
REM 强制清理所有8000端口的进程并重启
echo ============================================
echo 清理端口8000并重启后端
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] 查找占用8000端口的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo     发现进程 PID: %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo [2/4] 杀掉所有Python进程（确保清理干净）...
taskkill /F /IM python.exe 2>nul
if errorlevel 1 (
    echo     没有Python进程运行
) else (
    echo     已停止所有Python进程
)

timeout /t 2 /nobreak >nul

echo.
echo [3/4] 清理缓存...
if exist __pycache__ rmdir /s /q __pycache__
if exist .pytest_cache rmdir /s /q .pytest_cache
echo     缓存已清理

echo.
echo [4/4] 启动后端...
echo ============================================
echo 后端启动中...
echo 端口: 8000
echo 按 Ctrl+C 停止
echo ============================================
echo.

python main.py

pause
