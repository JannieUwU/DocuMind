@echo off
REM 重启后端服务脚本
echo ============================================
echo 重启后端服务
echo ============================================
echo.

REM 切换到backend目录
cd /d "%~dp0"

REM 杀掉所有python main.py进程
echo [1/3] 停止现有后端进程...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *main.py*" 2>nul
if errorlevel 1 (
    echo     没有发现运行中的后端进程
) else (
    echo     已停止后端进程
)

REM 等待1秒确保进程完全停止
timeout /t 1 /nobreak >nul

echo.
echo [2/3] 清理Python缓存...
REM 删除__pycache__目录
if exist __pycache__ (
    rmdir /s /q __pycache__
    echo     已清理缓存
) else (
    echo     无缓存需要清理
)

echo.
echo [3/3] 启动后端服务...
echo ============================================
echo 后端正在启动...
echo 按 Ctrl+C 可以停止服务
echo ============================================
echo.

REM 启动main.py
python main.py

pause
