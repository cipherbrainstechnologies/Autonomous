"""
Streamlit Application Entry Point
Wrapper for ui_frontend.py
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the main dashboard
from dashboard.ui_frontend import *

# Note: This file can be used as an alternative entry point
# Main entry point is ui_frontend.py as specified in deployment config

