#!/bin/bash
# Local Run Script for Linux/Mac - NIFTY Options Trading System
# This script runs the dashboard with logging enabled

echo "=================================================="
echo "NIFTY Options Trading System - Local Runner"
echo "=================================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.10 or higher."
    exit 1
fi

echo "[INFO] Python version:"
python3 --version
echo ""

# Check if requirements are installed
echo "[INFO] Checking dependencies..."
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "[WARNING] Dependencies may not be installed."
    echo "[INFO] Installing requirements..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies."
        exit 1
    fi
fi

echo "[INFO] Dependencies verified."
echo ""

# Initialize application
echo "[INFO] Initializing application..."
python3 main.py
if [ $? -ne 0 ]; then
    echo "ERROR: Application initialization failed."
    exit 1
fi

echo ""
echo "[INFO] Starting Streamlit dashboard..."
echo "[INFO] Dashboard will open at: http://localhost:8501"
echo "[INFO] Logs are being written to: logs/errors.log"
echo ""
echo "Press Ctrl+C to stop the server."
echo "=================================================="
echo ""

# Run Streamlit with explicit logging
python3 -m streamlit run dashboard/ui_frontend.py --server.headless=false --logger.level=info

