@echo off
echo ============================================================
echo  NeuroTranslate — Frontend Startup
echo ============================================================

node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

if not exist node_modules (
    echo Installing npm packages...
    npm install
)

echo.
echo Starting React + Vite dev server on http://localhost:5173
echo Make sure the backend is running on http://localhost:8000
echo Press Ctrl+C to stop.
echo.

npm run dev
