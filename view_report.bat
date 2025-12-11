@echo off
REM Quick script to open test report

echo Opening Selenium WebDriver Test Report...
echo.

REM Check if report exists
if exist tests\reports\test_report.html (
    echo Report found! Opening in browser...
    start tests\reports\test_report.html
    echo.
    echo Report opened in your default browser
) else (
    echo Report not found at: tests\reports\test_report.html
    echo Please run tests first: run_tests.bat --report
)

pause
