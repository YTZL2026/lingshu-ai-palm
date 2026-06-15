@echo off
title LingShu — AI Palm Trace

echo ========================================
echo   LingShu — AI Palm Trace v2.2
echo ========================================
echo.
echo [1/3] Checking Python...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3 first.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found

echo.
echo [2/3] Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies, please wait...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)
echo [OK] Dependencies ready

echo.
echo [3/3] Starting server...
echo.
echo ========================================
echo   Open in browser:
echo   http://localhost:8080
echo.
echo   Press Ctrl+C to stop
echo ========================================
echo.

python main.py

echo.
echo Server stopped.
pause
