"""
Main Application Entry Point for NIFTY Options Trading System
Coordinates engine and dashboard components
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logging with detailed format
log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt=date_format,
    handlers=[
        logging.FileHandler(log_dir / 'errors.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def initialize_application():
    """
    Initialize application components and verify configuration.
    """
    logger.info("Initializing NIFTY Options Trading System...")
    
    # Check required directories
    required_dirs = [
        'engine',
        'dashboard',
        'config',
        'data/historical',
        '.streamlit',
        'logs'
    ]
    
    for directory in required_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Verified directory: {directory}")
    
    # Check configuration files
    config_files = [
        'config/config.yaml',
        '.streamlit/secrets.toml'
    ]
    
    for config_file in config_files:
        if not Path(config_file).exists():
            logger.warning(f"Configuration file not found: {config_file}")
        else:
            logger.debug(f"Configuration file found: {config_file}")
    
    # Initialize trade log CSV if it doesn't exist
    from engine.trade_logger import TradeLogger
    trade_logger = TradeLogger()
    logger.info("Trade logger initialized")
    
    logger.info("Application initialization complete")


def main():
    """
    Main function - launches Streamlit dashboard.
    """
    try:
        # Initialize application
        initialize_application()
        
        logger.info("Starting Streamlit dashboard...")
        logger.info("Application ready. Access dashboard at the configured URL.")
        
        # Note: In production, this would be run via:
        # streamlit run dashboard/ui_frontend.py
        # This main.py serves as the entry point for coordination
        
        print("\n" + "="*50)
        print("NIFTY Options Trading System")
        print("="*50)
        print("\nTo start the dashboard, run:")
        print("  streamlit run dashboard/ui_frontend.py")
        print("\nOr for development:")
        print("  python main.py")
        print("="*50 + "\n")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

