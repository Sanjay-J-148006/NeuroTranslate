@echo off
echo ============================================================
echo  NeuroTranslate — Backend Startup
echo ============================================================

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10 or 3.11.
    pause
    exit /b 1
)

REM Activate venv if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo WARNING: No venv found. Running with system Python.
    echo Run: python -m venv venv ^& venv\Scripts\activate ^& pip install -r requirements.txt
)

REM Check .env exists
if not exist ..\\.env (
    echo WARNING: .env not found. Copying from .env.example...
    copy ..\\.env.example ..\\.env
)

REM Create required directories
if not exist ..\uploads mkdir ..\uploads
if not exist ..\exports mkdir ..\exports
if not exist logs mkdir logs

echo.
echo Starting FastAPI server on http://localhost:8000
echo API docs: http://localhost:8000/docs
echo Press Ctrl+C to stop.
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir pipeline --reload-dir utils --reload-dir routers --reload-dir services --reload-dir database --reload-dir models
