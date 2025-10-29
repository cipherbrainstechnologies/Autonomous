"""
Market Data Provider for fetching live OHLC data from SmartAPI
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta
import time
from logzero import logger

try:
    from SmartApi.smartConnect import SmartConnect
except ImportError:
    SmartConnect = None


class MarketDataProvider:
    """
    Provides market data fetching and aggregation for live trading.
    Handles OHLC data fetching, symbol token lookup, and timeframe aggregation.
    """
    
    def __init__(self, broker_instance):
        """
        Initialize MarketDataProvider with broker instance.
        
        Args:
            broker_instance: AngelOneBroker instance (for session management and API access)
        """
        if SmartConnect is None:
            raise ImportError(
                "smartapi-python not installed. Install with: pip install smartapi-python"
            )
        
        self.broker = broker_instance
        self.smart_api = broker_instance.smart_api
        
        # Cache NIFTY token (fetch once)
        self.nifty_token = None
        self.nifty_exchange = "NSE"
        
        # Data storage
        self._raw_data_buffer = []  # Store raw OHLC snapshots
        self._data_1h = pd.DataFrame()
        self._data_15m = pd.DataFrame()
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # 1 second between requests
        
        logger.info("MarketDataProvider initialized")
    
    def _rate_limit(self):
        """Ensure rate limiting (1 request per second)."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _get_nifty_token(self) -> Optional[str]:
        """
        Get NIFTY index symbol token from symbol master.
        Caches token to avoid repeated lookups.
        
        Returns:
            Symbol token string if found, None otherwise
        """
        if self.nifty_token is not None:
            return self.nifty_token
        
        try:
            if not self.broker._ensure_session():
                logger.error("Cannot fetch NIFTY token: No valid session")
                return None
            
            self._rate_limit()
            
            # Use broker's symbol search method
            # Try common NIFTY index symbols
            nifty_symbols = ["NIFTY", "NIFTY 50", "NIFTY50", "NIFTY INDEX"]
            
            for symbol in nifty_symbols:
                # Use broker's _search_symbol method (direct API call)
                symbol_result = self.broker._search_symbol(self.nifty_exchange, symbol)
                
                if not symbol_result:
                    continue
                
                # Parse response - check different possible response formats
                symbols = symbol_result.get('data', [])
                if not symbols:
                    symbols = symbol_result.get('fetched', [])
                
                if not symbols:
                    continue
                
                # Find exact match for NIFTY index (not futures/options)
                for sym in symbols:
                    tradingsymbol = sym.get('tradingsymbol', '').upper()
                    if 'NIFTY' in tradingsymbol and 'EQ' not in tradingsymbol and 'FUT' not in tradingsymbol and 'OPT' not in tradingsymbol:
                        self.nifty_token = sym.get('symboltoken')
                        self.nifty_tradingsymbol = sym.get('tradingsymbol')
                        logger.info(f"Found NIFTY token: {self.nifty_token} ({self.nifty_tradingsymbol})")
                        return self.nifty_token
            
            # Fallback: Use known NIFTY 50 token (common token: 99926000 for NIFTY 50 index)
            # This is a workaround if symbol search API doesn't work
            logger.warning("NIFTY token not found via search, trying known token")
            known_nifty_token = "99926000"  # Known NIFTY 50 index token on NSE
            
            # Verify the token works by trying to fetch market data
            test_ohlc = self.fetch_ohlc(known_nifty_token, self.nifty_exchange)
            if test_ohlc:
                self.nifty_token = known_nifty_token
                self.nifty_tradingsymbol = "NIFTY"
                logger.info(f"Using known NIFTY token: {self.nifty_token}")
                return self.nifty_token
            
            logger.error("NIFTY index not found and known token verification failed")
            return None
            
        except Exception as e:
            logger.exception(f"Error fetching NIFTY token: {e}")
            return None
    
    def fetch_ohlc(self, symbol_token: Optional[str] = None, exchange: str = "NSE", mode: str = "OHLC") -> Optional[Dict]:
        """
        Fetch OHLC data using SmartAPI Market Data API.
        
        Args:
            symbol_token: Symbol token (uses cached NIFTY token if None)
            exchange: Exchange code (default: "NSE")
            mode: Data mode - "LTP", "OHLC", or "FULL" (default: "OHLC")
        
        Returns:
            Dictionary with OHLC data or None if error
        """
        try:
            if not self.broker._ensure_session():
                logger.error("Cannot fetch OHLC: No valid session")
                return None
            
            # Use NIFTY token if not provided
            if symbol_token is None:
                symbol_token = self._get_nifty_token()
                if symbol_token is None:
                    logger.error("Cannot fetch OHLC: NIFTY token not available")
                    return None
            
            self._rate_limit()
            
            # Format request according to API spec
            request_params = {
                "mode": mode,
                "exchangeTokens": {
                    exchange: [symbol_token]
                }
            }
            
            # Call SmartAPI Market Data API
            # Note: SmartAPI Python library may need direct API call
            # Check if smart_api has marketQuote method or use requests directly
            try:
                # Try using SmartAPI's market data method if available
                response = self.smart_api.marketQuote(request_params)
            except AttributeError:
                # If method doesn't exist, use direct API call
                import requests
                
                if not self.broker.auth_token:
                    logger.error("Auth token not available for API call")
                    return None
                
                url = "https://apiconnect.angelone.in/rest/secure/angelbroking/market/v1/quote/"
                headers = {
                    "Authorization": f"Bearer {self.broker.auth_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-ClientLocalIP": "192.168.1.1",
                    "X-ClientPublicIP": "192.168.1.1",
                    "X-MACAddress": "00:00:00:00:00:00",
                    "X-PrivateKey": self.broker.api_key
                }
                
                response = requests.post(url, json=request_params, headers=headers)
                response = response.json()
            
            if response.get('status') == False or response.get('success') == False:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"Market data fetch failed: {error_msg}")
                return None
            
            # Parse response
            data = response.get('data', {})
            fetched = data.get('fetched', [])
            
            if not fetched:
                logger.warning("No data fetched from market data API")
                return None
            
            # Return first (and likely only) result
            market_data = fetched[0]
            
            logger.info(f"Fetched OHLC for {market_data.get('tradingSymbol', 'UNKNOWN')}: "
                       f"O={market_data.get('open')}, H={market_data.get('high')}, "
                       f"L={market_data.get('low')}, C={market_data.get('ltp', market_data.get('close'))}")
            
            return market_data
            
        except Exception as e:
            logger.exception(f"Error fetching OHLC: {e}")
            return None
    
    def get_historical_candles(
        self,
        symbol_token: Optional[str] = None,
        exchange: str = "NSE",
        interval: str = "ONE_MINUTE",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical candle data using SmartAPI getCandleData API.
        
        Args:
            symbol_token: Symbol token (uses cached NIFTY token if None)
            exchange: Exchange code (default: "NSE")
            interval: Time interval (ONE_MINUTE, FIVE_MINUTE, etc.)
            from_date: Start date in format "YYYY-MM-DD HH:mm"
            to_date: End date in format "YYYY-MM-DD HH:mm"
        
        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume or None
        """
        try:
            if not self.broker._ensure_session():
                logger.error("Cannot fetch historical candles: No valid session")
                return None
            
            if symbol_token is None:
                symbol_token = self._get_nifty_token()
                if symbol_token is None:
                    return None
            
            # Default to last 48 hours if dates not provided
            if to_date is None:
                to_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if from_date is None:
                from_datetime = datetime.now() - timedelta(hours=48)
                from_date = from_datetime.strftime("%Y-%m-%d %H:%M")
            
            self._rate_limit()
            
            # Format request for getCandleData
            params = {
                "exchange": exchange,
                "symboltoken": symbol_token,
                "interval": interval,
                "fromdate": from_date,
                "todate": to_date
            }
            
            # Call SmartAPI getCandleData
            response = self.smart_api.getCandleData(params)
            
            if response.get('status') == False:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"Historical candles fetch failed: {error_msg}")
                return None
            
            # Parse response
            # SmartAPI getCandleData may return data in different formats
            data = response.get('data', [])
            
            # If data is not a list, it might be a dict with nested structure
            if isinstance(data, dict):
                # Check for common nested formats
                data = data.get('fetched', data.get('data', []))
            
            if not data or len(data) == 0:
                logger.warning("No historical candle data returned")
                logger.debug(f"Response structure: {list(response.keys()) if isinstance(response, dict) else type(response)}")
                return None
            
            # Convert to DataFrame
            try:
                df = pd.DataFrame(data)
            except Exception as e:
                logger.error(f"Failed to convert response to DataFrame: {e}")
                logger.debug(f"Data sample: {data[:2] if isinstance(data, list) else data}")
                return None
            
            # Check if DataFrame is empty
            if df.empty:
                logger.warning("Empty DataFrame after conversion")
                return None
            
            # Standardize column names
            # SmartAPI may return different column names, adjust as needed
            # Ensure columns are strings before using .str accessor
            # Handle different column index types (RangeIndex, MultiIndex, etc.)
            try:
                # Convert to list of strings first, then back to Index
                column_names = [str(col).lower() for col in df.columns]
                df.columns = column_names
            except Exception as col_error:
                logger.error(f"Error converting column names: {col_error}")
                logger.debug(f"Column type: {type(df.columns)}, Columns: {list(df.columns)}")
                # Try alternative: rename columns if they exist
                if len(df.columns) > 0:
                    df.columns = [f"col_{i}" for i in range(len(df.columns))]
                else:
                    return None
            
            # Map columns to standard format
            if 'time' in df.columns:
                df['Date'] = pd.to_datetime(df['time'])
            elif 'datetime' in df.columns:
                df['Date'] = pd.to_datetime(df['datetime'])
            else:
                logger.warning("No timestamp column found in historical data")
                return None
            
            # Ensure we have OHLC columns
            column_mapping = {
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df[new_col] = df[old_col]
            
            # Select required columns
            required_cols = ['Date', 'Open', 'High', 'Low', 'Close']
            if 'Volume' in df.columns:
                required_cols.append('Volume')
            
            df = df[required_cols].copy()
            df = df.sort_values('Date').reset_index(drop=True)
            
            logger.info(f"Fetched {len(df)} historical candles from {from_date} to {to_date}")
            
            return df
            
        except Exception as e:
            logger.exception(f"Error fetching historical candles: {e}")
            return None
    
    def _aggregate_to_15m(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate raw (1-minute) data into 15-minute candles.
        
        Args:
            raw_data: DataFrame with 1-minute candles
        
        Returns:
            DataFrame with 15-minute candles
        """
        if raw_data.empty:
            return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        
        # Ensure Date is datetime
        if not pd.api.types.is_datetime64_any_dtype(raw_data['Date']):
            raw_data['Date'] = pd.to_datetime(raw_data['Date'])
        
        # Set Date as index for resampling
        df = raw_data.set_index('Date').copy()
        
        # Resample to 15 minutes
        aggregated = df.resample('15T').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum' if 'Volume' in df.columns else lambda x: 0
        })
        
        # Reset index
        aggregated = aggregated.reset_index()
        aggregated.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        
        # Remove rows with NaN (incomplete candles)
        aggregated = aggregated.dropna()
        
        return aggregated
    
    def _aggregate_to_1h(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate raw data into 1-hour candles.
        Can aggregate from 1-minute or 15-minute data.
        
        Args:
            raw_data: DataFrame with candles (1m or 15m)
        
        Returns:
            DataFrame with 1-hour candles
        """
        if raw_data.empty:
            return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        
        # Ensure Date is datetime
        if not pd.api.types.is_datetime64_any_dtype(raw_data['Date']):
            raw_data['Date'] = pd.to_datetime(raw_data['Date'])
        
        # Set Date as index for resampling
        df = raw_data.set_index('Date').copy()
        
        # Resample to 1 hour
        aggregated = df.resample('1H').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum' if 'Volume' in df.columns else lambda x: 0
        })
        
        # Reset index
        aggregated = aggregated.reset_index()
        aggregated.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        
        # Remove rows with NaN (incomplete candles)
        aggregated = aggregated.dropna()
        
        return aggregated
    
    def get_1h_data(self, window_hours: int = 48) -> pd.DataFrame:
        """
        Get 1-hour aggregated data.
        
        Args:
            window_hours: Number of hours of data to return (default: 48)
        
        Returns:
            DataFrame with 1-hour OHLC candles
        """
        # Try to get historical data first
        hist_data = self.get_historical_candles(
            interval="ONE_MINUTE",
            from_date=(datetime.now() - timedelta(hours=window_hours)).strftime("%Y-%m-%d %H:%M"),
            to_date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        
        if hist_data is not None and not hist_data.empty:
            # Aggregate to 1-hour
            self._data_1h = self._aggregate_to_1h(hist_data)
            
            # Trim to window
            if len(self._data_1h) > window_hours:
                self._data_1h = self._data_1h.tail(window_hours).copy()
        else:
            # Fallback: Fetch current OHLC and add to buffer
            ohlc = self.fetch_ohlc(mode="OHLC")
            if ohlc:
                current_time = datetime.now()
                new_row = pd.DataFrame([{
                    'Date': current_time.replace(minute=0, second=0, microsecond=0),
                    'Open': ohlc.get('open', 0),
                    'High': ohlc.get('high', 0),
                    'Low': ohlc.get('low', 0),
                    'Close': ohlc.get('ltp', ohlc.get('close', 0)),
                    'Volume': ohlc.get('tradeVolume', 0)
                }])
                
                if self._data_1h.empty:
                    self._data_1h = new_row
                else:
                    # Append or update
                    self._data_1h = pd.concat([self._data_1h, new_row], ignore_index=True)
                    self._data_1h = self._data_1h.drop_duplicates(subset=['Date'], keep='last')
                    self._data_1h = self._data_1h.sort_values('Date').reset_index(drop=True)
        
        return self._data_1h.tail(window_hours).copy() if not self._data_1h.empty else pd.DataFrame(
            columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        )
    
    def get_15m_data(self, window_hours: int = 12) -> pd.DataFrame:
        """
        Get 15-minute aggregated data.
        
        Args:
            window_hours: Number of hours of data to return (default: 12)
        
        Returns:
            DataFrame with 15-minute OHLC candles
        """
        # Try to get historical data first
        hist_data = self.get_historical_candles(
            interval="ONE_MINUTE",
            from_date=(datetime.now() - timedelta(hours=window_hours)).strftime("%Y-%m-%d %H:%M"),
            to_date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        
        if hist_data is not None and not hist_data.empty:
            # Aggregate to 15-minute
            self._data_15m = self._aggregate_to_15m(hist_data)
            
            # Trim to window
            max_candles = (window_hours * 60) // 15
            if len(self._data_15m) > max_candles:
                self._data_15m = self._data_15m.tail(max_candles).copy()
        else:
            # Fallback: Fetch current OHLC
            ohlc = self.fetch_ohlc(mode="OHLC")
            if ohlc:
                current_time = datetime.now()
                # Round down to nearest 15 minutes
                rounded_time = current_time.replace(minute=(current_time.minute // 15) * 15, second=0, microsecond=0)
                
                new_row = pd.DataFrame([{
                    'Date': rounded_time,
                    'Open': ohlc.get('open', 0),
                    'High': ohlc.get('high', 0),
                    'Low': ohlc.get('low', 0),
                    'Close': ohlc.get('ltp', ohlc.get('close', 0)),
                    'Volume': ohlc.get('tradeVolume', 0)
                }])
                
                if self._data_15m.empty:
                    self._data_15m = new_row
                else:
                    # Append or update
                    self._data_15m = pd.concat([self._data_15m, new_row], ignore_index=True)
                    self._data_15m = self._data_15m.drop_duplicates(subset=['Date'], keep='last')
                    self._data_15m = self._data_15m.sort_values('Date').reset_index(drop=True)
        
        return self._data_15m.tail((window_hours * 60) // 15).copy() if not self._data_15m.empty else pd.DataFrame(
            columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        )
    
    def refresh_data(self):
        """
        Refresh market data by fetching latest OHLC and updating buffers.
        This is called periodically by the live runner.
        """
        logger.info("Refreshing market data...")
        
        # Fetch latest data
        ohlc = self.fetch_ohlc(mode="OHLC")
        
        if ohlc:
            current_time = datetime.now()
            
            # Update 15-minute buffer
            rounded_15m = current_time.replace(minute=(current_time.minute // 15) * 15, second=0, microsecond=0)
            # Update 1-hour buffer
            rounded_1h = current_time.replace(minute=0, second=0, microsecond=0)
            
            # Try to get historical data for proper aggregation
            # Otherwise, just update with current OHLC
            hist_data = self.get_historical_candles(
                interval="ONE_MINUTE",
                from_date=(current_time - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
                to_date=current_time.strftime("%Y-%m-%d %H:%M")
            )
            
            if hist_data is not None and not hist_data.empty:
                # Re-aggregate from historical data
                self._data_15m = self._aggregate_to_15m(hist_data)
                self._data_1h = self._aggregate_to_1h(hist_data)
            else:
                # Fallback: Update with current snapshot
                if self._data_15m.empty or self._data_15m.iloc[-1]['Date'] < rounded_15m:
                    new_row_15m = pd.DataFrame([{
                        'Date': rounded_15m,
                        'Open': ohlc.get('open', 0),
                        'High': ohlc.get('high', 0),
                        'Low': ohlc.get('low', 0),
                        'Close': ohlc.get('ltp', ohlc.get('close', 0)),
                        'Volume': ohlc.get('tradeVolume', 0)
                    }])
                    self._data_15m = pd.concat([self._data_15m, new_row_15m], ignore_index=True)
                    self._data_15m = self._data_15m.drop_duplicates(subset=['Date'], keep='last')
                
                if self._data_1h.empty or self._data_1h.iloc[-1]['Date'] < rounded_1h:
                    new_row_1h = pd.DataFrame([{
                        'Date': rounded_1h,
                        'Open': ohlc.get('open', 0),
                        'High': ohlc.get('high', 0),
                        'Low': ohlc.get('low', 0),
                        'Close': ohlc.get('ltp', ohlc.get('close', 0)),
                        'Volume': ohlc.get('tradeVolume', 0)
                    }])
                    self._data_1h = pd.concat([self._data_1h, new_row_1h], ignore_index=True)
                    self._data_1h = self._data_1h.drop_duplicates(subset=['Date'], keep='last')
            
            logger.info("Market data refreshed successfully")
        else:
            logger.warning("Failed to refresh market data")

