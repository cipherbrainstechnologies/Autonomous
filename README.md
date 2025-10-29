# NIFTY Options Algo Trading System

A secure, cloud-ready algorithmic trading platform for NIFTY options trading using an Inside Bar + 15-minute Breakout strategy.

## 🎯 Features

- **Inside Bar Strategy**: Detects consolidation patterns followed by momentum breakouts
- **Secure Dashboard**: Streamlit-based web interface with authentication
- **Multi-Broker Support**: Abstract interface supporting Angel One and Fyers (extensible)
- **Trade Logging**: Comprehensive CSV-based trade journal with statistics
- **Backtesting Engine**: Historical strategy testing with detailed results
- **Cloud Ready**: Deploy to Render.com or any Python hosting platform

## 📁 Project Structure

```
nifty-options-trader/
│
├── engine/                   # Core strategy & logic
│   ├── strategy_engine.py     # Inside Bar detection & breakout confirmation
│   ├── signal_handler.py      # Signal processing and validation
│   ├── trade_logger.py        # CSV-based trade logging
│   ├── broker_connector.py    # Broker abstraction layer
│   └── backtest_engine.py     # Historical backtesting framework
│
├── dashboard/                # Streamlit UI
│   ├── ui_frontend.py        # Main dashboard application
│   └── streamlit_app.py      # Entry point wrapper
│
├── config/
│   └── config.yaml           # Strategy parameters
│
├── data/
│   └── historical/           # Historical data for backtesting
│
├── .streamlit/
│   └── secrets.toml          # Auth & API keys (git-ignored)
│
├── logs/
│   ├── trades.csv            # Trade journal
│   └── errors.log           # Application logs
│
├── memory-bank/              # Project documentation
│   ├── architecture.md
│   ├── flows/
│   └── patterns/
│
├── utils/
│   └── generate_password_hash.py  # Password hash generator
│
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Broker account (Angel One or Fyers)

### Installation

1. **Clone or download the repository**

```bash
cd nifty-options-trader
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

**Note**: Python 3.11+ includes TOML support. For Python < 3.11, `tomli` will be installed automatically.

3. **Generate password hash and cookie key**

```bash
python utils/generate_password_hash.py
```

This will generate:
- Password hash for authentication
- Random cookie key for session management

4. **Configure secrets**

Edit `.streamlit/secrets.toml`:

```toml
[credentials]
names = ["Your Name"]
usernames = ["your_username"]
passwords = ["$2b$12$YOUR_HASHED_PASSWORD_HERE"]

[cookie]
name = "nifty_auth"
key = "YOUR_RANDOM_KEY_HERE"
expiry_days = 30

[broker]
type = "angel"  # or "fyers"

# Angel One SmartAPI Configuration
api_key = "YOUR_API_KEY"
client_id = "YOUR_CLIENT_ID"  # e.g., "BBGV1001"
username = "YOUR_CLIENT_ID"  # Usually same as client_id
pwd = "YOUR_TRADING_PIN"  # Your trading pin
token = "YOUR_TOTP_QR_SECRET"  # TOTP QR secret for generating OTP
# Note: access_token is generated dynamically via session management

# Fyers Configuration (if using Fyers)
# api_secret = "YOUR_API_SECRET"  # Required for Fyers
# access_token = "YOUR_ACCESS_TOKEN"  # For Fyers
```

5. **Configure strategy parameters**

Edit `config/config.yaml`:

```yaml
lot_size: 75
strategy:
  type: inside_bar
  sl: 30              # Stop Loss in points
  rr: 1.8             # Risk-Reward Ratio
  filters:
    volume_spike: true
    avoid_open_range: true
```

6. **Verify setup** (Optional but recommended)

```bash
python verify_setup.py
```

This will check all dependencies, configuration, and setup.

7. **Start the dashboard**

```bash
# Option 1: Direct run (recommended)
python -m streamlit run dashboard/ui_frontend.py

# Option 2: Use run script (with enhanced logging)
# Windows:
.\run_local.bat

# Linux/Mac:
chmod +x run_local.sh
./run_local.sh
```

The dashboard will open in your browser at `http://localhost:8501`

**For detailed local run instructions and troubleshooting, see [LOCAL_RUN.md](LOCAL_RUN.md)**

**Note**: If you get "streamlit is not recognized" error, use `python -m streamlit` instead. See [STREAMLIT_FIX.md](STREAMLIT_FIX.md) for details.

## 📖 Architecture Overview

### Strategy Logic

1. **Inside Bar Detection**: Scans 1-hour timeframe for candles completely contained within previous candle's range
2. **Breakout Confirmation**: Monitors 15-minute timeframe for volume-confirmed breakouts
3. **Signal Generation**: Valid signals trigger trade execution logic
4. **Order Execution**: Broker API integration places orders with SL/TP
5. **Trade Logging**: All trades logged with entry/exit, PnL, and reasoning

### Components

- **Strategy Engine**: Core pattern detection and signal generation
- **Signal Handler**: Validates signals against filters and rules
- **Broker Connector**: Abstract interface for multiple broker APIs
- **Trade Logger**: CSV-based comprehensive trade history
- **Backtest Engine**: Historical strategy testing with simulation
- **Dashboard**: Streamlit web interface with authentication

## 🔐 Security

- Password-based authentication via `streamlit-authenticator`
- Secrets stored in `.streamlit/secrets.toml` (git-ignored)
- Session-based cookie authentication
- Configurable token expiry

## 📊 Dashboard Features

### Dashboard Tab
- Real-time algo status and controls
- Active trades monitoring
- System information and statistics
- Start/Stop algorithm controls

### Trade Journal Tab
- Complete trade history
- Trade statistics (win rate, P&L, etc.)
- CSV export functionality
- Detailed performance metrics

### Backtest Tab
- Upload historical CSV data
- Run backtests with configurable parameters
- View equity curve and trade details
- Comprehensive performance analysis

### Settings Tab
- View current configuration
- Broker connection status
- System information

## 🧪 Backtesting

The backtesting engine allows you to test the strategy on historical data:

1. Prepare CSV file with columns: `Date`, `Open`, `High`, `Low`, `Close`, `Volume`
2. Upload via the Backtest tab in the dashboard
3. Configure parameters (initial capital, lot size)
4. Run backtest and analyze results

## 🔌 Broker Integration

### Angel One SmartAPI

The system includes full SmartAPI-Python integration for Angel One:

#### Setup Instructions

1. **Obtain API Credentials**:
   - Login to [Angel One SmartAPI Developer Portal](https://smartapi.angelone.in/)
   - Create an app and get your `api_key`
   - Note your `client_id` (user ID)

2. **Configure TOTP Authentication**:
   - Enable TOTP (Time-based One-Time Password) in your Angel One account
   - Scan the QR code with an authenticator app (Google Authenticator, Authy, etc.)
   - Copy the TOTP secret key (or extract from QR code)
   - Add the secret to `secrets.toml` as `token`

3. **Configure Trading Pin**:
   - Your trading pin is the PIN you use for trading on the Angel One platform
   - Add this to `secrets.toml` as `pwd`

4. **Session Management**:
   - Sessions are automatically generated on first API call
   - Use the "Refresh Broker Session" button in the Settings tab to manually refresh
   - Sessions automatically refresh when tokens expire

#### SmartAPI Features Implemented

- ✅ Session generation with TOTP authentication
- ✅ Automatic token refresh
- ✅ Symbol token lookup from symbol master
- ✅ Order placement (MARKET and LIMIT)
- ✅ Position tracking
- ✅ Order cancellation and modification
- ✅ Order status checking
- ✅ Comprehensive error handling and logging

#### Symbol Format

NIFTY options symbols must be formatted as: `NIFTY{DD}{MON}{YY}{STRIKE}{CE/PE}`

Example: `NIFTY29OCT2419000CE` for NIFTY 19000 Call expiring 29 Oct 2024

**Note**: The system currently uses a placeholder expiry date. In production, you should:
- Fetch current NIFTY expiry dates from market data
- Automatically select the nearest expiry
- Format the symbol accordingly

### Fyers API

Fyers integration is available as a placeholder. Full implementation pending.

### Adding Broker Implementation

To implement a new broker:

1. Extend the `BrokerInterface` class in `engine/broker_connector.py`
2. Implement required methods:
   - `place_order()`
   - `get_positions()`
   - `cancel_order()`
   - `get_order_status()`
   - `modify_order()`

3. Add broker type to factory function `create_broker_interface()`

## ☁️ Deployment to Render.com

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/nifty-options-trader.git
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to [Render.com](https://render.com)
2. Create new **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run dashboard/ui_frontend.py --server.port=$PORT --server.address=0.0.0.0`
5. Add environment variables or use Render's secrets manager:
   - Convert `.streamlit/secrets.toml` to environment variables if needed
6. Deploy and bookmark your dashboard URL

### Alternative: Local Deployment

For local deployment, simply run:

```bash
streamlit run dashboard/ui_frontend.py
```

## 📝 Configuration

### Strategy Parameters (`config/config.yaml`)

- `lot_size`: Number of lots per trade
- `strategy.sl`: Stop loss in points
- `strategy.rr`: Risk-reward ratio
- `strategy.filters.volume_spike`: Enable volume spike filter
- `strategy.filters.avoid_open_range`: Avoid trading in first 30 minutes

### Broker Configuration (`.streamlit/secrets.toml`)

- Broker type (angel/fyers)
- API credentials
- Access tokens

## 🛠️ Development

### Running Tests

```bash
# Run application initialization
python main.py
```

### Project Structure

- `engine/`: Core trading logic
- `dashboard/`: Streamlit UI components
- `config/`: Configuration files
- `utils/`: Utility scripts

## 📚 Documentation

- **Architecture**: See `memory-bank/architecture.md`
- **Patterns**: See `memory-bank/patterns/`
- **Project Rules**: See `.cursorrules`

## ⚠️ Important Notes

1. **Broker API Integration**: 
   - **Angel One SmartAPI**: Fully implemented and ready for use (after configuration)
   - **Fyers**: Placeholder implementation - requires full integration
   - Always test in paper trading/sandbox environment first
   - Ensure TOTP token is kept secure and not shared

2. **Risk Management**: This system is for educational purposes. Always:
   - Test thoroughly in paper trading mode
   - Start with small position sizes
   - Monitor trades closely
   - Understand the risks involved

3. **Data Requirements**: For backtesting, ensure historical data has:
   - Consistent date/time format
   - OHLC (Open, High, Low, Close) values
   - Volume data

## 🤝 Contributing

This is a standalone trading system. For enhancements:

1. Follow the architecture patterns in `memory-bank/`
2. Update documentation as changes are made
3. Test thoroughly before deploying

## 📄 License

This project is provided as-is for educational and research purposes.

## 🔑 TODO (Manual Steps)

- [ ] Generate password hash using `utils/generate_password_hash.py`
- [ ] Configure `.streamlit/secrets.toml` with credentials
- [ ] Set up broker API keys and access tokens
- [ ] Add historical CSV data for backtesting
- [ ] Implement full broker API integration
- [ ] Test in paper trading environment
- [ ] Deploy to Render.com or preferred hosting

## 📞 Support

For issues and questions:
1. Review `memory-bank/architecture.md` for system design
2. Check logs in `logs/errors.log`
3. Verify configuration files are correctly set up

---

**Disclaimer**: Trading involves substantial risk of loss. This software is for educational purposes only. Always test thoroughly and use at your own risk.
