# NIFTY Options Algo Trading System - Architecture

## System Overview

The NIFTY Options Algo Trading System is a secure, cloud-ready algorithmic trading platform designed for NIFTY options trading using an Inside Bar + 15-minute Breakout strategy.

## Architecture Components

### 1. Core Engine (`engine/`)
- **strategy_engine.py**: Core strategy logic for Inside Bar detection and breakout confirmation
- **signal_handler.py**: Signal processing, validation, and trade signal generation
- **trade_logger.py**: Comprehensive trade logging to CSV format
- **broker_connector.py**: Abstract broker interface supporting multiple broker APIs (Angel One, Fyers)
- **backtest_engine.py**: Historical backtesting framework with trade simulation

### 2. Dashboard (`dashboard/`)
- **ui_frontend.py**: Main Streamlit application with authentication
- **streamlit_app.py**: Application entry point wrapper

### 3. Configuration (`config/`)
- **config.yaml**: Strategy parameters, lot sizes, SL/TP, filters
- **.streamlit/secrets.toml**: Secure credentials and broker API keys

### 4. Data Management
- **data/historical/**: Historical market data for backtesting
- **logs/**: Application logs and trade journal CSV files

## System Flow

1. **Strategy Detection**: 1-hour timeframe scanned for Inside Bar patterns
2. **Breakout Confirmation**: 15-minute timeframe monitored for volume-confirmed breakouts
3. **Signal Generation**: Valid signals trigger trade execution logic
4. **Order Execution**: Broker API integration places orders with SL/TP
5. **Trade Logging**: All trades logged with entry/exit, PnL, and reasoning
6. **Dashboard Monitoring**: Real-time dashboard provides control and visibility

## Technology Stack

- **Frontend**: Streamlit with streamlit-authenticator
- **Backend**: Python 3.10+
- **Data Processing**: Pandas, NumPy
- **Configuration**: YAML, TOML
- **Broker APIs**: Angel One SmartAPI, Fyers API (extensible)

## Security Model

- Password-based authentication via streamlit-authenticator
- Secrets stored in `.streamlit/secrets.toml` (git-ignored)
- Session-based cookie authentication
- Configurable expiry for security tokens

## Deployment Architecture

- **Platform**: Render.com (Web Service)
- **Runtime**: Python 3.10+
- **Start Command**: `streamlit run dashboard/ui_frontend.py`
- **Secrets Management**: Environment variables or Render secrets config

## Strategy Logic

### Inside Bar Pattern Detection (1H Timeframe)
- Detects when a candle is completely contained within the previous candle's range
- Pattern condition: `current_high < prev_high AND current_low > prev_low`
- Requires at least 2 candles of historical data
- Uses the most recent Inside Bar to mark breakout range

### Breakout Confirmation (15m Timeframe)
- Monitors last 5 candles on 15-minute timeframe for breakout
- Checks each candle (oldest to newest) for valid breakout
- **Bullish Breakout (CE)**: Close > range_high AND Volume > threshold
- **Bearish Breakout (PE)**: Close < range_low AND Volume > threshold
- Volume threshold = Average volume of last 5 candles × multiplier (default 1.0)
- Direction determines Call (CE) or Put (PE) option selection

### Strike Selection
- ATM (At The Money) based on current NIFTY price
- Strike rounded to nearest 50 (NIFTY strikes are multiples of 50)
- Configurable `atm_offset` parameter for strike adjustment (default: 0)

### Risk Management
- Fixed Stop Loss (configurable, default 30 points)
- Risk-Reward Ratio (configurable, default 1.8)
- Stop Loss: Entry - sl_points
- Take Profit: Entry + (sl_points × rr_ratio)
- Volume spike filter (optional)
- Open range avoidance filter (optional)

### Signal Output
- Direction (CE/PE)
- Strike price
- Entry price
- Stop Loss level
- Take Profit level
- Range high/low
- Signal reason and timestamp

