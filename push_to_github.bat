@echo off
REM GitHub Setup and Push Script
REM This script helps you push your project to GitHub

echo ================================================
echo Vue3 RAG - GitHub Push Helper
echo ================================================
echo.

echo This script will help you push your project to GitHub.
echo.
echo PREREQUISITES:
echo 1. You have a GitHub account
echo 2. You have created a new repository on GitHub
echo 3. You have the repository URL ready
echo.
echo ================================================
echo.

REM Check if git is configured
git config user.name >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Git user not configured globally
    echo The local user is already set for this project
    echo.
)

REM Check current status
echo [INFO] Current Git Status:
git status --short
echo.

REM Ask for GitHub repository URL
echo ================================================
echo GitHub Repository Setup
echo ================================================
echo.
echo Please create a new repository on GitHub first:
echo 1. Go to: https://github.com/new
echo 2. Repository name: vue3-rag-hybrid-search (or your choice)
echo 3. Description: Vue3 RAG Hybrid Search Application
echo 4. Choose: Private or Public
echo 5. DO NOT initialize with README, .gitignore, or license
echo 6. Click "Create repository"
echo.
echo After creating, you'll see a URL like:
echo https://github.com/YOUR_USERNAME/vue3-rag-hybrid-search.git
echo.

set /p REPO_URL="Enter your GitHub repository URL: "

if "%REPO_URL%"=="" (
    echo [ERROR] No URL provided. Exiting.
    pause
    exit /b 1
)

echo.
echo [INFO] Adding remote repository...
git remote add origin %REPO_URL% 2>nul

if %errorlevel% neq 0 (
    echo [INFO] Remote 'origin' already exists. Updating URL...
    git remote set-url origin %REPO_URL%
)

echo [SUCCESS] Remote repository configured
echo.

REM Show remote info
echo [INFO] Remote repository:
git remote -v
echo.

REM Ask for confirmation
set /p CONFIRM="Push to GitHub now? (y/n): "

if /i not "%CONFIRM%"=="y" (
    echo.
    echo [INFO] Push cancelled. You can push later with:
    echo git push -u origin master
    echo.
    pause
    exit /b 0
)

echo.
echo [INFO] Pushing to GitHub...
echo This may take a few minutes depending on your connection...
echo.

git push -u origin master

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo SUCCESS!
    echo ================================================
    echo.
    echo Your project has been pushed to GitHub!
    echo.
    echo Repository URL: %REPO_URL%
    echo.
    echo Next steps:
    echo 1. Visit your repository on GitHub
    echo 2. Add repository description and topics
    echo 3. Review README.md
    echo 4. Invite collaborators if needed
    echo.
    echo To view your repository:
    start %REPO_URL:.git=%
) else (
    echo.
    echo [ERROR] Push failed!
    echo.
    echo Common issues:
    echo 1. Authentication failed - you may need to use a Personal Access Token
    echo 2. Repository doesn't exist or URL is wrong
    echo 3. No permission to push
    echo.
    echo To create a Personal Access Token:
    echo 1. Go to: https://github.com/settings/tokens
    echo 2. Click "Generate new token" -^> "Generate new token (classic)"
    echo 3. Select scopes: repo (all)
    echo 4. Click "Generate token"
    echo 5. Copy the token and use it as your password when pushing
    echo.
    echo Try again with:
    echo git push -u origin master
    echo.
)

pause
