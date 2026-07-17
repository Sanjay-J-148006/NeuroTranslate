@echo off
echo ============================================================
echo  NeuroTranslate — Full Install Script (Run Once)
echo ============================================================

echo.
echo [1/4] Creating .env from template...
if not exist .env (
    copy .env.example .env
    echo .env created successfully.
) else (
    echo .env already exists — skipping.
)

echo.
echo [2/4] Creating directories...
if not exist uploads mkdir uploads
if not exist exports mkdir exports
if not exist backend\logs mkdir backend\logs

echo.
echo [3/4] Creating Python virtual environment...
cd backend
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo [4/4] Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

cd ..

echo.
echo [5/5] Installing frontend npm packages...
cd frontend
npm install
cd ..

echo.
echo ============================================================
echo  Installation complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Run backend:  cd backend ^& start_backend.bat
echo   2. Run frontend: cd frontend ^& start_frontend.bat
echo   3. Open: http://localhost:5173
echo.
pause
