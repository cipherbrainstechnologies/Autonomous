"""
Secure Streamlit Dashboard for NIFTY Options Trading System
"""

# -*- coding: utf-8 -*-
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
from datetime import datetime
import os
import sys

# TOML support - use tomllib (Python 3.11+) or tomli package
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback: tomli package
    except ImportError:
        # Last resort: use toml package (older API - different method signature)
        try:
            import toml
            # Create a wrapper class to match tomllib API
            class TomlWrapper:
                @staticmethod
                def load(file):
                    # toml.load() expects text mode, not binary
                    if hasattr(file, 'read'):
                        content = file.read()
                        if isinstance(content, bytes):
                            content = content.decode('utf-8')
                        return toml.loads(content)
                    return toml.load(file)
            tomllib = TomlWrapper()
        except ImportError:
            tomllib = None

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.strategy_engine import check_for_signal
from engine.trade_logger import TradeLogger, log_trade
from engine.broker_connector import create_broker_interface
from engine.signal_handler import SignalHandler
from engine.backtest_engine import BacktestEngine


# Page config
st.set_page_config(
    page_title="NIFTY Options Trading System",
    page_icon="📈",
    layout="wide"
)

# Load configuration
@st.cache_data
def load_config():
    """Load configuration from secrets.toml"""
    secrets_path = '.streamlit/secrets.toml'
    if not os.path.exists(secrets_path):
        st.error("❌ secrets.toml not found. Please create it in .streamlit/ directory.")
        st.stop()
    
    # Load TOML file (not YAML!)
    if tomllib is None:
        st.error("❌ TOML parser not available. Install with: pip install tomli")
        st.stop()
    
    try:
        with open(secrets_path, 'rb') as file:  # TOML requires binary mode
            config = tomllib.load(file)
        return config
    except Exception as e:
        st.error(f"❌ Error loading secrets.toml: {e}")
        st.stop()

# Initialize authentication
config = load_config()

try:
    # Convert credentials from list format to dict format expected by streamlit-authenticator
    # TOML format: names=["Admin"], usernames=["admin"], passwords=["hash"]
    # Library expects: usernames={"admin": "Admin"}, passwords={"admin": "hash"}
    cred_config = config['credentials']
    
    # Convert lists to dict: {username: name} and {username: password}
    usernames_list = cred_config.get('usernames', [])
    names_list = cred_config.get('names', [])
    passwords_list = cred_config.get('passwords', [])
    
    # Create dict format
    credentials_dict = {
        'usernames': {},
        'names': {},
        'passwords': {}
    }
    
    for i, username in enumerate(usernames_list):
        credentials_dict['usernames'][username] = names_list[i] if i < len(names_list) else username
        credentials_dict['names'][username] = names_list[i] if i < len(names_list) else username
        credentials_dict['passwords'][username] = passwords_list[i] if i < len(passwords_list) else ""
    
    # streamlit-authenticator expects credentials dict with usernames/names/passwords as dicts
    authenticator = stauth.Authenticate(
        credentials=credentials_dict,
        cookie_name=config['cookie']['name'],
        cookie_key=config['cookie']['key'],
        cookie_expiry_days=float(config['cookie']['expiry_days']),
        auto_hash=False  # Passwords are already hashed
    )
except Exception as e:
    st.error(f"❌ Authentication setup failed: {e}")
    st.exception(e)  # Show full traceback for debugging
    st.stop()

# Login - New API behavior:
# - location='main' or 'sidebar': Renders widget, returns None
# - location='unrendered': Returns tuple (name, auth_status, username) without rendering widget
# Strategy: Use unrendered to check status first, then show login widget if needed

login_result = authenticator.login(location='unrendered', key='Login_check')

if login_result is None:
    # Not authenticated - show login widget and stop
    st.header("🔐 Login Required")
    st.info("Please enter your credentials to access the trading system.")
    # This will render the login widget - when user submits, page will reload
    authenticator.login(location='main', key='Login_widget')
    st.stop()
else:
    name, auth_status, username = login_result
    
    # Check authentication status
    if not auth_status:
        if auth_status == False:
            st.error("❌ Invalid credentials. Please try again.")
            authenticator.login(location='main', key='Login_widget')
            st.stop()
        else:
            st.warning("🔒 Authentication status unknown. Please log in.")
            authenticator.login(location='main', key='Login_widget')
            st.stop()

# Main Dashboard (after authentication)
st.sidebar.success(f"👋 Welcome, {name}")

# Initialize session state
if 'algo_running' not in st.session_state:
    st.session_state.algo_running = False
if 'broker' not in st.session_state:
    try:
        st.session_state.broker = create_broker_interface(config)
    except Exception as e:
        st.session_state.broker = None
        st.warning(f"Broker initialization warning: {e}")
if 'signal_handler' not in st.session_state:
    # Load strategy config
    import yaml as yaml_lib
    with open('config/config.yaml', 'r') as f:
        strategy_config = yaml_lib.safe_load(f)
    st.session_state.signal_handler = SignalHandler(strategy_config)
if 'trade_logger' not in st.session_state:
    st.session_state.trade_logger = TradeLogger()

# Sidebar menu
tab = st.sidebar.radio(
    "📋 Menu",
    ["Dashboard", "Trade Journal", "Backtest", "Settings"],
    index=0
)

# Logout button - API: button_name (first), location (second), key (named)
authenticator.logout(button_name='Logout', location='sidebar', key='Logout')

# ============ DASHBOARD TAB ============
if tab == "Dashboard":
    st.header("📈 Live Algo Status")
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        engine_status = "🟢 Running" if st.session_state.algo_running else "🔴 Stopped"
        st.metric("Engine Status", engine_status)
    
    with col2:
        broker_type = config['broker']['type'].capitalize() if config.get('broker') else "Not Configured"
        st.metric("Broker", broker_type)
    
    with col3:
        # Get active signals count
        active_signals = st.session_state.signal_handler.get_active_signals()
        st.metric("Active Trades", len(active_signals))
    
    st.divider()
    
    # Control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start Algo", disabled=st.session_state.algo_running, use_container_width=True):
            st.session_state.algo_running = True
            st.success("✅ Algorithm started")
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Algo", disabled=not st.session_state.algo_running, use_container_width=True):
            st.session_state.algo_running = False
            st.warning("⏸️ Algorithm stopped")
            st.rerun()
    
    st.divider()
    
    # Active Trades Section
    st.subheader("📊 Active Trades")
    active_signals = st.session_state.signal_handler.get_active_signals()
    
    if active_signals:
        trades_df = pd.DataFrame(active_signals)
        st.dataframe(trades_df, use_container_width=True)
    else:
        st.info("ℹ️ No active trades")
    
    # System Information
    st.divider()
    st.subheader("ℹ️ System Information")
    
    # Load strategy config
    import yaml as yaml_lib
    with open('config/config.yaml', 'r') as f:
        strategy_config = yaml_lib.safe_load(f)
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write("**Strategy Parameters:**")
        st.write(f"- Lot Size: {strategy_config.get('lot_size', 'N/A')}")
        st.write(f"- Stop Loss: {strategy_config.get('strategy', {}).get('sl', 'N/A')} points")
        st.write(f"- Risk-Reward: {strategy_config.get('strategy', {}).get('rr', 'N/A')}")
    
    with info_col2:
        st.write("**Filters:**")
        filters = strategy_config.get('strategy', {}).get('filters', {})
        st.write(f"- Volume Spike: {'✅' if filters.get('volume_spike') else '❌'}")
        st.write(f"- Avoid Open Range: {'✅' if filters.get('avoid_open_range') else '❌'}")

# ============ TRADE JOURNAL TAB ============
elif tab == "Trade Journal":
    st.header("📘 Trade Log")
    
    trade_logger = st.session_state.trade_logger
    
    # Get all trades
    all_trades = trade_logger.get_all_trades()
    
    if not all_trades.empty:
        # Display trades
        st.subheader("All Trades")
        st.dataframe(all_trades, use_container_width=True)
        
        # Statistics
        st.divider()
        st.subheader("📊 Trade Statistics")
        
        stats = trade_logger.get_trade_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", stats['total_trades'])
        
        with col2:
            st.metric("Win Rate", f"{stats['win_rate']:.2f}%")
        
        with col3:
            st.metric("Total P&L", f"₹{stats['total_pnl']:,.2f}")
        
        with col4:
            avg_pnl = (stats['avg_win'] + stats['avg_loss']) / 2 if stats['total_trades'] > 0 else 0
            st.metric("Avg P&L", f"₹{avg_pnl:,.2f}")
        
        # Detailed stats
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Winning Trades:**")
            st.write(f"- Count: {stats['winning_trades']}")
            st.write(f"- Avg Win: ₹{stats['avg_win']:,.2f}")
        
        with col2:
            st.write("**Losing Trades:**")
            st.write(f"- Count: {stats['losing_trades']}")
            st.write(f"- Avg Loss: ₹{stats['avg_loss']:,.2f}")
        
        # Download CSV
        st.download_button(
            label="📥 Download Trade Log (CSV)",
            data=all_trades.to_csv(index=False).encode('utf-8'),
            file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("ℹ️ No trades logged yet")

# ============ BACKTEST TAB ============
elif tab == "Backtest":
    st.header("🧪 Backtest Strategy")
    
    # Backtest options
    st.subheader("Upload Historical Data")
    
    uploaded_file = st.file_uploader(
        "Choose CSV file with historical OHLC data",
        type=['csv'],
        help="CSV should have columns: Date, Open, High, Low, Close, Volume"
    )
    
    if uploaded_file is not None:
        try:
            # Load data
            data = pd.read_csv(uploaded_file)
            
            # Ensure date column is datetime
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
                data.set_index('Date', inplace=True)
            
            # Display data preview
            st.subheader("Data Preview")
            st.dataframe(data.head(10), use_container_width=True)
            
            st.divider()
            
            # Backtest parameters
            st.subheader("Backtest Parameters")
            
            col1, col2 = st.columns(2)
            
            with col1:
                initial_capital = st.number_input(
                    "Initial Capital (₹)",
                    min_value=10000,
                    value=100000,
                    step=10000
                )
            
            with col2:
                # Load strategy config
                import yaml as yaml_lib
                with open('config/config.yaml', 'r') as f:
                    strategy_config = yaml_lib.safe_load(f)
                
                lot_size = st.number_input(
                    "Lot Size",
                    min_value=1,
                    value=strategy_config.get('lot_size', 75),
                    step=1
                )
            
            # Run backtest
            if st.button("▶️ Run Backtest", use_container_width=True):
                with st.spinner("Running backtest..."):
                    try:
                        # Prepare config
                        backtest_config = {
                            'strategy': strategy_config.get('strategy', {}),
                            'lot_size': lot_size
                        }
                        
                        # Initialize engine
                        engine = BacktestEngine(backtest_config)
                        
                        # Run backtest (simplified: using same data for 1h and 15m)
                        results = engine.run_backtest(data, data, initial_capital)
                        
                        # Display results
                        st.subheader("📊 Backtest Results")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Trades", results['total_trades'])
                        
                        with col2:
                            st.metric("Win Rate", f"{results['win_rate']:.2f}%")
                        
                        with col3:
                            st.metric("Total P&L", f"₹{results['total_pnl']:,.2f}")
                        
                        with col4:
                            st.metric("Return %", f"{results['return_pct']:.2f}%")
                        
                        # Detailed results
                        st.write(f"**Initial Capital:** ₹{results['initial_capital']:,.2f}")
                        st.write(f"**Final Capital:** ₹{results['final_capital']:,.2f}")
                        st.write(f"**Winning Trades:** {results['winning_trades']}")
                        st.write(f"**Losing Trades:** {results['losing_trades']}")
                        st.write(f"**Average Win:** ₹{results['avg_win']:,.2f}")
                        st.write(f"**Average Loss:** ₹{results['avg_loss']:,.2f}")
                        st.write(f"**Max Drawdown:** {results['max_drawdown']:.2f}%")
                        
                        # Equity curve
                        if results.get('equity_curve'):
                            st.subheader("Equity Curve")
                            equity_df = pd.DataFrame({
                                'Capital': results['equity_curve']
                            })
                            st.line_chart(equity_df)
                        
                        # Trades table
                        if results.get('trades'):
                            st.subheader("Trade Details")
                            trades_df = pd.DataFrame(results['trades'])
                            st.dataframe(trades_df, use_container_width=True)
                    
                    except Exception as e:
                        st.error(f"❌ Backtest failed: {e}")
                        st.exception(e)
        
        except Exception as e:
            st.error(f"❌ Error loading CSV file: {e}")
            st.exception(e)
    
    else:
        st.info("ℹ️ Please upload a CSV file with historical OHLC data to run backtest")

# ============ SETTINGS TAB ============
elif tab == "Settings":
    st.header("⚙️ Configuration")
    
    # Load current config
    import yaml as yaml_lib
    with open('config/config.yaml', 'r') as f:
        current_config = yaml_lib.safe_load(f)
    
    st.subheader("Strategy Parameters")
    
    # Editable config (read-only for now - can be enhanced with file editing)
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Trading Parameters:**")
        st.text(f"Lot Size: {current_config.get('lot_size', 'N/A')}")
        
        st.write("**Strategy Settings:**")
        strategy = current_config.get('strategy', {})
        st.text(f"Type: {strategy.get('type', 'N/A')}")
        st.text(f"Stop Loss: {strategy.get('sl', 'N/A')} points")
        st.text(f"Risk-Reward: {strategy.get('rr', 'N/A')}")
    
    with col2:
        st.write("**Filters:**")
        filters = strategy.get('filters', {})
        st.text(f"Volume Spike: {'Enabled' if filters.get('volume_spike') else 'Disabled'}")
        st.text(f"Avoid Open Range: {'Enabled' if filters.get('avoid_open_range') else 'Disabled'}")
    
    st.warning("⚠️ To modify configuration, edit `config/config.yaml` file directly and restart the application.")
    
    st.divider()
    
    # Broker configuration info
    st.subheader("Broker Configuration")
    if config.get('broker'):
        broker_config = config['broker']
        st.text(f"Type: {broker_config.get('type', 'N/A')}")
        st.text(f"Client ID: {broker_config.get('client_id', 'N/A')}")
        st.success("✅ Broker configured")
    else:
        st.error("❌ Broker not configured")
    
    st.divider()
    
    # System info
    st.subheader("System Information")
    st.text(f"Python Version: {sys.version.split()[0]}")
    st.text(f"Streamlit Version: {st.__version__}")

