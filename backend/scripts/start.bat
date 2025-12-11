@echo off
set EMAIL_PASSWORD=xajhzindwfrwbgde
"%~dp0venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
