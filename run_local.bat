@echo off
REM Local Run Script for Windows - NIFTY Options Trading System
REM This script runs the dashboard with logging enabled

echo ==================================================
echo NIFTY Options Trading System - Local Runner
echo ==================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo [INFO] Python version:
python --version
echo.

REM Check if requirements are installed
echo [INFO] Checking dependencies...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Dependencies may not be installed.
    echo [INFO] Installing requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo [INFO] Dependencies verified.
echo.

REM Initialize application
echo [INFO] Initializing application...
python main.py
if errorlevel 1 (
    echo ERROR: Application initialization failed.
    pause
    exit /b 1
)

echo.
echo [INFO] Starting Streamlit dashboard...
echo [INFO] Dashboard will open at: http://localhost:8501
echo [INFO] Logs are being written to: logs/errors.log
echo.
echo Press Ctrl+C to stop the server.
echo ==================================================
echo.

REM Run Streamlit with explicit logging (use python -m streamlit for better Windows compatibility)
python -m streamlit run dashboard/ui_frontend.py --server.headless=false --logger.level=info

pause

