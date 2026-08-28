@echo off
echo =================================================
echo  0xPDFForge — ZIP to PDF Documentation Platform
echo  Starting server at http://127.0.0.1:8000
echo =================================================
where python >nul 2>&1
if %errorlevel% neq 0 (
  echo Python not found. Install Python 3.10+ from https://python.org
  pause
  exit /b 1
)
python -m pip install -q -r requirements.txt
if %errorlevel% neq 0 (
  echo Failed to install dependencies
  pause
  exit /b 1
)
echo.
echo Opening browser...
start http://127.0.0.1:8000
echo Server running — press Ctrl+C to stop
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
