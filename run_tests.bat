@echo off
REM Run Selenium WebDriver Tests - Windows Script
REM This script sets up and runs the test suite

echo ================================================
echo Vue3 RAG - Selenium WebDriver Test Suite
echo ================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup_tests.bat first
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo [INFO] Virtual environment activated
echo.

REM Check if services are running
echo [INFO] Checking if frontend is running...
curl -s http://localhost:5173 >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Frontend may not be running at http://localhost:5173
    echo Please start frontend with: npm run dev
    echo.
)

echo [INFO] Checking if backend is running...
curl -s http://localhost:8000/docs >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Backend may not be running at http://localhost:8000
    echo Please start backend with: python -m uvicorn main:app --reload
    echo.
)

REM Parse command line arguments
set TEST_FILE=
set TEST_MARKERS=
set HEADLESS=false
set REPORT=false

:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="-h" set HEADLESS=true
if "%~1"=="--headless" set HEADLESS=true
if "%~1"=="-r" set REPORT=true
if "%~1"=="--report" set REPORT=true
if "%~1"=="-m" (
    set TEST_MARKERS=%~2
    shift
)
shift
goto parse_args
:end_parse

echo ================================================
echo Running Tests
echo ================================================
echo.

REM Build pytest command
set PYTEST_CMD=pytest tests/ -v --tb=short

REM Add markers if specified
if not "%TEST_MARKERS%"=="" (
    set PYTEST_CMD=%PYTEST_CMD% -m "%TEST_MARKERS%"
    echo [INFO] Running tests with markers: %TEST_MARKERS%
)

REM Add HTML report if requested
if "%REPORT%"=="true" (
    set PYTEST_CMD=%PYTEST_CMD% --html=tests/reports/test_report.html --self-contained-html
    echo [INFO] HTML report will be generated
)

REM Set headless mode
if "%HEADLESS%"=="true" (
    set HEADLESS=true
    echo [INFO] Running in headless mode
)

echo.
echo [INFO] Executing: %PYTEST_CMD%
echo.

REM Run tests
%PYTEST_CMD%

set EXIT_CODE=%errorlevel%

echo.
echo ================================================
echo Test Execution Complete
echo ================================================
echo Exit Code: %EXIT_CODE%

if "%REPORT%"=="true" (
    echo.
    echo [INFO] HTML report generated at: tests/reports/test_report.html
)

REM Deactivate virtual environment
deactivate

exit /b %EXIT_CODE%
