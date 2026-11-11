@echo off
setlocal
cd /d "%~dp0"

echo ======================================================================
echo  TextVigil - Backend, ML ^& Frontend Verification Suite
echo ======================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Running setup.bat first...
    call "%~dp0setup.bat"
    if %ERRORLEVEL% neq 0 exit /b 1
)

set PYTHONUTF8=1

echo [*] Running Python ML, OCR, Threat Rules, History ^& API tests...
".venv\Scripts\python.exe" -m pytest -v tests/ --cov=src --cov-report=term-missing
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Python backend/ML tests failed.
    exit /b 1
)

echo [*] Running Frontend TypeScript typecheck...
call npm --prefix frontend run typecheck
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Frontend TypeScript check failed.
    exit /b 1
)

echo [PASS] All TextVigil backend, ML, and frontend checks passed!
endlocal
