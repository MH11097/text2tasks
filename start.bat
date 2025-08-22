@echo off
setlocal EnableDelayedExpansion

echo Text2Tasks - Clean Architecture Startup
echo ===========================================
echo.

REM Check if .env exists
if not exist .env (
    echo .env file not found!
    if exist .env.example (
        echo Copying .env.example to .env...
        copy .env.example .env >nul
        echo Please edit .env with your actual values (OpenAI API key, etc.)
    ) else (
        echo .env.example not found either. You may need to create .env manually.
    )
    echo.
)

REM Backend Setup
echo Setting up Backend...
echo ========================

REM Check Python version
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH
        echo Please install Python from https://python.org/
        pause
        exit /b 1
    )
    set PYTHON_CMD=python3
    echo Using python3
) else (
    set PYTHON_CMD=python
    echo Using python
)

REM Check if virtual environment exists
if not exist .wvenv (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv .wvenv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)

REM Activate virtual environment
echo Activating virtual environment...
if exist .wvenv\Scripts\activate.bat (
    call .wvenv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo ERROR: Virtual environment activation script not found
    pause
    exit /b 1
)

REM Install/upgrade dependencies
if exist requirements.txt (
    echo Installing Python dependencies...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install Python dependencies
        pause
        exit /b 1
    )
    echo Python dependencies installed successfully
) else (
    echo WARNING: requirements.txt not found, skipping Python dependencies
)

REM Frontend Setup
echo.
call setup_frontend.bat
if errorlevel 1 (
    set FRONTEND_AVAILABLE=false
) else (
    set FRONTEND_AVAILABLE=true
)

echo.
echo DEBUG: Reached setup complete section
echo Setup complete!
echo ==================
echo DEBUG: FRONTEND_AVAILABLE = %FRONTEND_AVAILABLE%

REM Check for main application file
if not exist app\main.py (
    echo ERROR: app\main.py not found!
    echo Please make sure you're in the correct project directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Backend: http://localhost:8000
echo API docs: http://localhost:8000/docs

if "%FRONTEND_AVAILABLE%"=="true" (
    echo Frontend: http://localhost:5174
    
    echo.
    echo Starting Frontend in separate window...
    start "Text2Tasks Frontend" cmd /k "cd /d %CD%\frontend && npm run dev"
    
    REM Give frontend time to start
    timeout /t 2 /nobreak >nul
    
    echo Frontend started in separate window
    echo Starting backend in this window...
) else (
    echo Frontend: Not available
    echo.
    echo Starting Backend only...
    echo Press Ctrl+C to stop the server
    echo.
)

echo.
echo Starting Backend...
%PYTHON_CMD% -m app.main

echo.
echo Backend has stopped
pause