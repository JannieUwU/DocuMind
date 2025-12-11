@echo off
REM Setup Test Environment - Windows Script
REM This script installs all test dependencies

echo ================================================
echo Vue3 RAG - Test Environment Setup
echo ================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    exit /b 1
)

echo [INFO] Python found
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo [INFO] Virtual environment activated
echo.

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install test dependencies
echo [INFO] Installing test dependencies...
pip install -r tests\requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)

echo.
echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Start your backend: cd backend ^&^& python -m uvicorn main:app --reload
echo 2. Start your frontend: cd frontend ^&^& npm run dev
echo 3. Run tests: run_tests.bat
echo.
echo Available test commands:
echo - run_tests.bat                    (Run all tests)
echo - run_tests.bat --headless         (Run without browser window)
echo - run_tests.bat --report           (Generate HTML report)
echo - run_tests.bat -m "navigation"    (Run tests with specific marker)
echo.

deactivate
