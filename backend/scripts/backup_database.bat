@echo off
REM Database Backup Script
REM Run: backup_database.bat

setlocal enabledelayedexpansion

REM Get current date and time
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set BACKUP_DATE=%datetime:~0,8%
set BACKUP_TIME=%datetime:~8,6%

REM Create backups directory if it doesn't exist
if not exist "backups" mkdir backups

REM Backup filename
set BACKUP_FILE=backups\users_backup_%BACKUP_DATE%_%BACKUP_TIME%.db

REM Copy database
echo ========================================
echo Database Backup Utility
echo ========================================
echo.
echo Source: users.db
echo Destination: %BACKUP_FILE%
echo.

if exist "users.db" (
    copy "users.db" "%BACKUP_FILE%"
    if errorlevel 1 (
        echo [ERROR] Backup failed!
        exit /b 1
    ) else (
        echo [SUCCESS] Database backed up successfully!
        echo.

        REM Get file size
        for %%A in ("%BACKUP_FILE%") do set SIZE=%%~zA
        echo Backup file size: !SIZE! bytes
        echo.

        REM List recent backups
        echo Recent backups:
        dir /b /o-d backups\users_backup_*.db 2>nul | findstr /n "^" | findstr "^[1-5]:"
        echo.

        REM Count total backups
        for /f %%A in ('dir /b backups\users_backup_*.db 2^>nul ^| find /c /v ""') do set COUNT=%%A
        echo Total backups: !COUNT!

        REM Warn if too many backups
        if !COUNT! GTR 10 (
            echo.
            echo [WARNING] You have more than 10 backups.
            echo Consider deleting old backups to save space.
            echo Run: cleanup_old_backups.bat
        )
    )
) else (
    echo [ERROR] users.db not found!
    exit /b 1
)

echo.
echo ========================================
pause
