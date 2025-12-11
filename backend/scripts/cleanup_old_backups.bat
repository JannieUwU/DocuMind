@echo off
REM Cleanup Old Backups Script
REM Keeps only the 5 most recent backups

setlocal enabledelayedexpansion

echo ========================================
echo Cleanup Old Database Backups
echo ========================================
echo.

if not exist "backups" (
    echo No backups directory found.
    exit /b 0
)

REM Count current backups
for /f %%A in ('dir /b backups\users_backup_*.db 2^>nul ^| find /c /v ""') do set COUNT=%%A

echo Current backups: !COUNT!
echo.

if !COUNT! LEQ 5 (
    echo No cleanup needed. You have 5 or fewer backups.
    echo.
    pause
    exit /b 0
)

echo Keeping 5 most recent backups...
echo Deleting older backups...
echo.

REM Get list of files sorted by date (oldest first) and delete all but last 5
set DELETED=0
set /a KEEP=!COUNT!-5

for /f "skip=%KEEP% delims=" %%F in ('dir /b /o-d backups\users_backup_*.db') do (
    echo Deleting: %%F
    del "backups\%%F"
    set /a DELETED+=1
)

echo.
echo ========================================
echo Deleted !DELETED! old backup(s)
echo Remaining backups: 5
echo ========================================
echo.

REM List remaining backups
echo Remaining backups:
dir /b /o-d backups\users_backup_*.db

echo.
pause
