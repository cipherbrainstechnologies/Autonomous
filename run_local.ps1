# PowerShell Local Run Script for NIFTY Options Trading System
# This script runs the dashboard with logging enabled

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "NIFTY Options Trading System - Local Runner" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Get current script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if Python is available
Write-Host "[INFO] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Python not found. Please install Python 3.10 or higher." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[INFO] Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.10 or higher." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check if requirements are installed
Write-Host "[INFO] Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import streamlit" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] Dependencies may not be installed." -ForegroundColor Yellow
        Write-Host "[INFO] Installing requirements..." -ForegroundColor Yellow
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host "[INFO] Dependencies verified." -ForegroundColor Green
    }
} catch {
    Write-Host "[WARNING] Could not verify dependencies, attempting to install..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""

# Initialize application
Write-Host "[INFO] Initializing application..." -ForegroundColor Yellow
try {
    python main.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Application initialization failed." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} catch {
    Write-Host "[WARNING] Application initialization check failed, continuing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[INFO] Starting Streamlit dashboard..." -ForegroundColor Green
Write-Host "[INFO] Dashboard will open at: http://localhost:8501" -ForegroundColor Green
Write-Host "[INFO] Logs are being written to: logs/errors.log" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Run Streamlit with explicit logging (use python -m streamlit for better Windows compatibility)
try {
    python -m streamlit run dashboard/ui_frontend.py --server.headless=false --logger.level=info
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to start Streamlit." -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Trying alternative method..." -ForegroundColor Yellow
    # Try direct streamlit if python -m doesn't work
    & streamlit run dashboard/ui_frontend.py --server.headless=false --logger.level=info
    if ($LASTEXITCODE -ne 0) {
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Read-Host "Press Enter to exit"

