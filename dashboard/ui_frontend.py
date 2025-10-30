"""
Secure Streamlit Dashboard for NIFTY Options Trading System
"""

# -*- coding: utf-8 -*-
import streamlit as st
# import streamlit_authenticator as stauth  # Temporarily disabled
import yaml
from yaml.loader import SafeLoader
import pandas as pd
from datetime import datetime
import os
import sys
from logzero import logger

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
from engine.market_data import MarketDataProvider
from engine.live_runner import LiveStrategyRunner


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

# ===================================================================
# AUTHENTICATION TEMPORARILY DISABLED - Bypass due to library bugs
# ===================================================================
# TODO: Re-enable authentication once streamlit-authenticator issues are resolved
# Known issues:
# - Version 0.4.2: "string indices must be integers" error during password validation
# - Version 0.2.3: Various API compatibility issues
# ===================================================================

# Load config (still needed for broker settings, etc.)
config = load_config()

# Authentication bypass - Set user as "Admin" for now
name = "Admin"
username = "admin"
auth_status = True

# Show bypass notice in sidebar
st.sidebar.warning("⚠️ Authentication disabled - Development mode")
st.sidebar.info("🔓 Direct access enabled")

# Main Dashboard
st.sidebar.success(f"👋 Welcome, {name}")

# ===================================================================
# COMMENTED OUT AUTHENTICATION CODE (for reference)
# ===================================================================
# try:
#     # Convert credentials from list format to dict format expected by streamlit-authenticator
#     # TOML format: names=["Admin"], usernames=["admin"], passwords=["hash"]
#     # Library expects: usernames={"admin": "Admin"}, passwords={"admin": "hash"}
#     cred_config = config['credentials']
#     
#     # Convert lists to dict: {username: name} and {username: password}
#     usernames_list = cred_config.get('usernames', [])
#     names_list = cred_config.get('names', [])
#     passwords_list = cred_config.get('passwords', [])
#     
#     # Create dict format
#     credentials_dict = {
#         'usernames': {},
#         'names': {},
#         'passwords': {}
#     }
#     
#     for i, username in enumerate(usernames_list):
#         credentials_dict['usernames'][username] = names_list[i] if i < len(names_list) else username
#         credentials_dict['names'][username] = names_list[i] if i < len(names_list) else username
#         password_value = passwords_list[i] if i < len(passwords_list) else ""
#         credentials_dict['passwords'][username] = password_value
#     
#     # Validate passwords before creating authenticator
#     # Version 0.2.3: Accepts plain text passwords and auto-hashes them
#     # Simple validation - check password exists and length
#     for username, password_value in credentials_dict['passwords'].items():
#         if not password_value or password_value == "":
#             st.error(f"❌ Password is empty for user '{username}'.")
#             st.error("   Please add a plain text password to secrets.toml")
#             st.error("   Example: passwords = [\"admin\"]")
#             st.stop()
#         
#         # Version 0.2.3 works best with plain text passwords (auto-hashes them)
#         # If it's a hash (starts with $2b$), show warning but allow it
#         if password_value.startswith('$2b$'):
#             if len(password_value) != 60:
#                 st.error(f"❌ Password hash for user '{username}' is invalid (length: {len(password_value)}, expected: 60)")
#                 st.error("   **SOLUTION:** Use plain text password - version 0.2.3 will hash it automatically")
#                 st.stop()
#             else:
#                 st.warning(f"⚠️ You're using a pre-hashed password for '{username}'.")
#                 st.warning("   Version 0.2.3 works better with plain text passwords.")
#         else:
#             # Plain text password - perfect for version 0.2.3
#             if len(password_value) < 3:
#                 st.warning(f"⚠️ Password for '{username}' is very short. Consider using a stronger password.")
#     
#     # Version 0.2.3 API: positional parameters (credentials, cookie_name, key, cookie_expiry_days)
#     # Note: Version 0.2.3 doesn't have auto_hash parameter - it auto-hashes plain text passwords
#     try:
#         authenticator = stauth.Authenticate(
#             credentials_dict,  # Positional: credentials dict
#             config['cookie']['name'],  # Positional: cookie_name
#             config['cookie']['key'],  # Positional: key (cookie key)
#             float(config['cookie']['expiry_days'])  # Positional: cookie_expiry_days
#         )
#     except Exception as auth_init_error:
#         st.error(f"❌ Failed to initialize authenticator: {auth_init_error}")
#         st.error("Please check that secrets.toml has valid credentials format.")
#         st.exception(auth_init_error)
#         st.stop()
# except Exception as e:
#     st.error(f"❌ Authentication setup failed: {e}")
#     st.exception(e)  # Show full traceback for debugging
#     st.stop()
#
# # Login - Version 0.2.3 API: login(form_name: str, location: str = 'main') -> tuple
# # Returns: (name, authentication_status, username)
# # If not authenticated, shows login widget and returns (None, None, None)
#
# try:
#     name, auth_status, username = authenticator.login("Login", "main")
# except Exception as login_error:
#     st.error(f"❌ Login error: {login_error}")
#     st.error("This might be due to invalid credentials structure. Please check secrets.toml format.")
#     st.exception(login_error)
#     st.stop()
#
# # Check authentication status
# if not auth_status:
#     if auth_status == False:
#         st.error("❌ Invalid username/password")
#     else:
#         st.warning("🔒 Please log in to access the trading system")
#     st.stop()
#
# # Main Dashboard (after authentication)
# st.sidebar.success(f"👋 Welcome, {name}")

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

# Initialize market data provider (only if broker is available)
if 'market_data_provider' not in st.session_state:
    if st.session_state.broker is not None:
        try:
            st.session_state.market_data_provider = MarketDataProvider(st.session_state.broker)
        except Exception as e:
            st.session_state.market_data_provider = None
            st.warning(f"Market data provider initialization warning: {e}")
    else:
        st.session_state.market_data_provider = None

# Initialize live runner (lazy - only when needed)
if 'live_runner' not in st.session_state:
    # Load full config (with market_data section)
    import yaml as yaml_lib
    with open('config/config.yaml', 'r') as f:
        full_config = yaml_lib.safe_load(f)
    
    if (st.session_state.broker is not None and 
        st.session_state.market_data_provider is not None and
        'signal_handler' in st.session_state and
        'trade_logger' in st.session_state):
        try:
            st.session_state.live_runner = LiveStrategyRunner(
                market_data_provider=st.session_state.market_data_provider,
                signal_handler=st.session_state.signal_handler,
                broker=st.session_state.broker,
                trade_logger=st.session_state.trade_logger,
                config=full_config
            )
        except Exception as e:
            st.session_state.live_runner = None
            st.warning(f"Live runner initialization warning: {e}")
    else:
        st.session_state.live_runner = None

# Sidebar menu
tab = st.sidebar.radio(
    "📋 Menu",
    ["Dashboard", "Trade Journal", "Backtest", "Settings"],
    index=0
)

# Logout button - DISABLED (authentication bypassed)
# authenticator.logout("Logout", "sidebar")

# ============ DASHBOARD TAB ============
if tab == "Dashboard":
    st.header("📈 Live Algo Status")
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
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

    with col4:
        # NIFTY current live price (LTP)
        ltp_text = "—"
        try:
            if st.session_state.market_data_provider is not None:
                ohlc = st.session_state.market_data_provider.fetch_ohlc(mode="LTP")
                if isinstance(ohlc, dict):
                    ltp_val = ohlc.get('ltp')
                    if ltp_val is None:
                        ltp_val = ohlc.get('close')
                    if ltp_val is not None:
                        ltp_text = f"{float(ltp_val):.2f}"
        except Exception:
            pass
        st.metric("NIFTY LTP", ltp_text)
    
    st.divider()
    # Auto-refresh toggle (10s)
    auto = st.checkbox("Auto-refresh every 10 seconds", value=True)
    if auto:
        import time as _t
        st.caption("Auto-refresh enabled")
        # Trigger rerun after rendering at the bottom of the page
    
    # Control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start Algo", disabled=st.session_state.algo_running, use_container_width=True):
            if st.session_state.live_runner is None:
                st.error("❌ Live runner not initialized. Check broker configuration.")
            else:
                try:
                    success = st.session_state.live_runner.start()
                    if success:
                        st.session_state.algo_running = True
                        st.success("✅ Algorithm started - Monitoring live market data...")
                    else:
                        st.error("❌ Failed to start algorithm. Check logs for details.")
                except Exception as e:
                    st.error(f"❌ Error starting algorithm: {e}")
                    logger.exception(e)
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Algo", disabled=not st.session_state.algo_running, use_container_width=True):
            if st.session_state.live_runner is not None:
                try:
                    success = st.session_state.live_runner.stop()
                    if success:
                        st.session_state.algo_running = False
                        st.warning("⏸️ Algorithm stopped")
                    else:
                        st.error("❌ Failed to stop algorithm")
                except Exception as e:
                    st.error(f"❌ Error stopping algorithm: {e}")
                    logger.exception(e)
            else:
                st.session_state.algo_running = False
            st.rerun()
    
    # Live data status
    if st.session_state.algo_running and st.session_state.live_runner is not None:
        st.divider()
        st.subheader("📡 Live Data Status")
        
        status = st.session_state.live_runner.get_status()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Status", "🟢 Running" if status['running'] else "🔴 Stopped")
        
        with col2:
            st.metric("Cycles Completed", status['cycle_count'])
        
        with col3:
            if status['last_fetch_time']:
                fetch_time = datetime.fromisoformat(status['last_fetch_time'])
                st.metric("Last Data Fetch", fetch_time.strftime("%H:%M:%S"))
            else:
                st.metric("Last Data Fetch", "Never")
        
        with col4:
            if status['last_signal_time']:
                signal_time = datetime.fromisoformat(status['last_signal_time'])
                st.metric("Last Signal", signal_time.strftime("%H:%M:%S"))
            else:
                st.metric("Last Signal", "None")
        
        # Show error count if any
        if status['error_count'] > 0:
            st.warning(f"⚠️ {status['error_count']} errors encountered. Check logs for details.")
        
        # Manual refresh button
        if st.button("🔄 Refresh Market Data Now"):
            try:
                if st.session_state.market_data_provider:
                    st.session_state.market_data_provider.refresh_data()
                    st.success("✅ Market data refreshed")
                else:
                    st.error("❌ Market data provider not available")
            except Exception as e:
                st.error(f"❌ Error refreshing data: {e}")
                logger.exception(e)
    
    st.divider()
    
    # Live NIFTY Chart and Option Data
    st.subheader("📈 NIFTY Index – Live 15m Chart")
    if st.session_state.market_data_provider is not None:
        try:
            df15 = st.session_state.market_data_provider.get_15m_data(
                window_hours=st.session_state.live_runner.config.get('market_data', {}).get('data_window_hours_15m', 12)
            ) if st.session_state.live_runner else pd.DataFrame()
            # Ensure buffers are populated if historical fetch fails
            if st.session_state.market_data_provider:
                try:
                    st.session_state.market_data_provider.refresh_data()
                except Exception:
                    pass
            if df15 is not None and not df15.empty:
                chart_df = df15.set_index('Date')[['Close']]
                st.line_chart(chart_df, width='stretch')
            else:
                st.info("No 15m data available yet.")
        except Exception as e:
            st.warning(f"Chart error: {e}")
    else:
        st.info("Market data provider not initialized.")

    st.divider()
    st.subheader("📐 Option Greeks (NIFTY – next Tuesday expiry)")
    try:
        if st.session_state.broker is not None:
            greeks = st.session_state.broker.get_option_greeks("NIFTY")
            if greeks:
                greeks_df = pd.DataFrame(greeks)
                # Keep key columns visible
                keep_cols = [c for c in [
                    'name','expiry','strikePrice','optionType','delta','gamma','theta','vega','impliedVolatility','tradeVolume'
                ] if c in greeks_df.columns]
                st.dataframe(greeks_df[keep_cols], width='stretch', height=300)
            else:
                st.info("No Greeks data returned.")
        else:
            st.info("Broker not initialized.")
    except Exception as e:
        st.warning(f"Greeks error: {e}")

    st.divider()

    # Active Trades Section
    st.subheader("📊 Active Trades")
    active_signals = st.session_state.signal_handler.get_active_signals()
    
    if active_signals:
        trades_df = pd.DataFrame(active_signals)
        st.dataframe(trades_df, width='stretch')
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

    # Perform auto-refresh rerun at the end to avoid interrupting rendering
    if auto:
        import time as _t
        _t.sleep(10)
        st.rerun()

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
        broker_type = broker_config.get('type', '').lower()
        st.text(f"Type: {broker_config.get('type', 'N/A')}")
        st.text(f"Client ID: {broker_config.get('client_id', 'N/A')}")
        st.success("✅ Broker configured")
        
        # Token refresh button for Angel One SmartAPI
        if broker_type == 'angel':
            st.divider()
            st.write("**Session Management**")
            
            # Initialize broker interface in session state if not exists
            if 'broker_interface' not in st.session_state:
                try:
                    st.session_state.broker_interface = create_broker_interface(config)
                except Exception as e:
                    st.error(f"❌ Failed to initialize broker: {e}")
                    st.session_state.broker_interface = None
            
            if st.session_state.broker_interface is not None:
                if st.button("🔄 Refresh Broker Session", type="primary"):
                    with st.spinner("Refreshing broker session..."):
                        try:
                            success = st.session_state.broker_interface.refresh_session()
                            if success:
                                st.success("✅ Broker session refreshed successfully!")
                            else:
                                st.error("❌ Failed to refresh session. Check logs for details.")
                        except Exception as e:
                            st.error(f"❌ Error refreshing session: {e}")
                
                st.info("💡 Session tokens expire periodically. Refresh when needed or on first order.")
            else:
                st.warning("⚠️ Broker interface not initialized. Check configuration.")
    else:
        st.error("❌ Broker not configured")
    
    st.divider()
    
    # System info
    st.subheader("System Information")
    st.text(f"Python Version: {sys.version.split()[0]}")
    st.text(f"Streamlit Version: {st.__version__}")

