@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ======================================================================
echo  TextVigil - Windows Setup and Environment Initialization
echo ======================================================================

:: 1. Locate Python 3.12+ (prefer Python 3.12 launcher if available)
set PYTHON_CMD=
py -3.12 --version >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py -3.12
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set PYTHON_CMD=python
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python 3.10+ was not found on PATH.
    echo Install Python 3.12 from https://www.python.org/downloads/ and add it to PATH.
    exit /b 1
)

for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do set PYTHON_VER=%%i
echo [*] Detected %PYTHON_VER%

:: 2. Create project virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating virtual environment (.venv)...
    %PYTHON_CMD% -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment (.venv) already exists.
)

:: 3. Install Python dependencies
echo [*] Installing Python dependencies from requirements.txt...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    exit /b 1
)
echo [OK] Python dependencies installed.

:: 4. Install and build React frontend
where npm >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js / npm was not found on PATH.
    echo Install Node.js 20+ from https://nodejs.org/ and add it to PATH.
    exit /b 1
)

echo [*] Installing frontend npm packages...
call npm --prefix frontend install
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install frontend packages.
    exit /b 1
)

echo [*] Building frontend production bundle...
call npm --prefix frontend run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Frontend build failed.
    exit /b 1
)
echo [OK] Frontend built cleanly.

:: 5. Initialize directories and .env (never overwrite existing .env)
if not exist "data" mkdir data
if not exist "data\raw" mkdir data\raw
if not exist "models" mkdir models

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [OK] Created .env from .env.example.
) else (
    echo [OK] Existing .env preserved.
)

:: 6. Download UCI dataset & train ML models if missing
echo [*] Verifying UCI SMS Spam Collection dataset and trained models...
".venv\Scripts\python.exe" scripts\download_dataset.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to obtain UCI SMS Spam Collection dataset.
    exit /b 1
)

if not exist "models\messageshield_models.joblib" (
    echo [*] Training TF-IDF + Logistic Regression & Multinomial Naive Bayes models...
    ".venv\Scripts\python.exe" scripts\train_models.py
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Model training failed.
        exit /b 1
    )
) else (
    echo [OK] Trained model artifacts already exist in models\.
)

".venv\Scripts\python.exe" scripts\generate_demo_assets.py >nul

:: 7. Check Tesseract availability for Screenshot OCR
".venv\Scripts\python.exe" -c "from src.core.ocr_processor import get_ocr_status; ok, msg = get_ocr_status(); print('[OK] OCR:', msg) if ok else print('[WARN] OCR unavailable:', msg, '(Text & CSV scanning still work; install Tesseract for screenshot OCR.)')"

echo ======================================================================
echo  TextVigil Setup Complete!
echo    - Launch App : run.bat
echo    - Run Tests  : test.bat
echo ======================================================================
endlocal
