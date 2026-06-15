@echo off
title MedRec Builder
echo ============================================
echo   Medical Record QC Ledger - EXE Builder
echo ============================================
echo.

:: Check Python
echo [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.11+ first.
    pause & exit /b 1
)
python --version

:: Install PyInstaller
echo.
echo [2/4] Installing PyInstaller...
pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller install failed
    pause & exit /b 1
)

:: Install flask only (skip heavy deps)
echo.
echo [3/4] Installing Flask...
pip install flask --quiet

:: Build
echo.
echo [4/4] Building EXE...

if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

pyinstaller --onefile --console --name="MedRecLedger" ^
    --add-data="static;static" ^
    --add-data="config.json;." ^
    --hidden-import=flask ^
    --collect-all=flask ^
    medrec_server.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed
    pause & exit /b 1
)

:: Copy data files
echo.
echo Copying data files...

set "SRC=..\training-map\病历质控测试组"
set "DST=dist\data\病历质控测试组"

mkdir "%DST%\_extracted" 2>nul
mkdir "%DST%\_analysis" 2>nul
for %%w in (A组 C组 D组) do (
    mkdir "%DST%\%%w" 2>nul
)

if exist "%SRC%" (
    for %%w in (A组 C组 D组) do (
        if exist "%SRC%\%%w\*.xps" xcopy /Y "%SRC%\%%w\*.xps" "%DST%\%%w\" >nul 2>&1
    )
    if exist "%SRC%\_extracted\*.txt" xcopy /Y "%SRC%\_extracted\*.txt" "%DST%\_extracted\" >nul 2>&1
    if exist "%SRC%\_analysis\*.json" xcopy /Y "%SRC%\_analysis\*.json" "%DST%\_analysis\" >nul 2>&1
) else (
    echo WARNING: Source data not found at %SRC%
    echo Data directory created empty. Add XPS files to dist\data\ later.
)

copy /Y "config.json" "dist\" >nul 2>&1

:: Rename exe
if exist "dist\MedRecLedger.exe" (
    ren "dist\MedRecLedger.exe" "病历质控台账生成器.exe" 2>nul
)

echo.
echo ============================================
echo   BUILD SUCCESS!
echo.
echo   Output: dist\病历质控台账生成器.exe
echo   Data:   dist\data\ (XPS + analysis)
echo.
echo   To use:
echo   1. Open dist folder
echo   2. Double-click EXE
echo   3. Browser: http://localhost:8081
echo   4. Enter DeepSeek API Key in toolbar
echo ============================================
pause
