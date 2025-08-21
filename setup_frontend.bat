@echo off
REM Frontend Setup Script
echo Setting up Frontend...
echo =========================

set FRONTEND_AVAILABLE=false

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Node.js is not installed. Please install Node.js to run the frontend.
    echo You can download it from: https://nodejs.org/
    echo Will start backend only...
    exit /b 0
)

echo Node.js found: 
node --version

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo npm is not available
    exit /b 0
)

echo npm found:
npm --version

REM Check if frontend directory exists
if not exist frontend (
    echo Frontend directory not found - this might be a backend-only project
    exit /b 0
)

echo Frontend directory found

REM Check if package.json exists
if not exist frontend\package.json (
    echo ERROR: package.json not found in frontend directory
    exit /b 1
)

echo Installing frontend dependencies...
pushd frontend
npm install
if errorlevel 1 (
    echo WARNING: Failed to install frontend dependencies
    popd
    exit /b 1
)

echo Frontend dependencies installed successfully
popd
set FRONTEND_AVAILABLE=true
exit /b 0