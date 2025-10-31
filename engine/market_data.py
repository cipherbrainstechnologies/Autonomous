"""
Market Data Provider for fetching live OHLC data from SmartAPI
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta
import time
from logzero import logger

# Retry configuration for resilient API calls
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

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
    
    def _is_candle_complete(self, candle_time: datetime, timeframe_minutes: int) -> bool:
        """
        Check if a candle is complete based on current time.
        
        A candle is complete when the current time has passed the next candle's start time.
        Example:
        - 15m candle at 10:30 is complete at 10:45 (15 min after start)
        - 1h candle at 10:00 is complete at 11:00 (1 hour after start)
        
        Args:
            candle_time: Start time of the candle (datetime or Timestamp, may be timezone-aware)
            timeframe_minutes: Timeframe in minutes (15 or 60)
        
        Returns:
            True if candle is complete, False if still forming
        """
        # Get current time in IST (timezone-naive, but assume IST)
        # Note: datetime.now() returns local time (which should be IST for Indian systems)
        current_time = datetime.now()
        
        # Normalize candle_time: if it's timezone-aware (from API), convert to IST-naive
        # Convert pandas Timestamp to Python datetime if needed
        if hasattr(candle_time, 'to_pydatetime'):
            candle_time = candle_time.to_pydatetime()
        
        # If candle_time is timezone-aware, convert to IST then remove timezone info
        if candle_time.tzinfo is not None:
            # Convert to IST first, then remove timezone info
            try:
                import pytz
                ist = pytz.timezone('Asia/Kolkata')
                if candle_time.tzinfo != ist:
                    # Convert to IST
                    candle_time = candle_time.astimezone(ist)
                # Remove timezone info to make it naive (IST)
                candle_time = candle_time.replace(tzinfo=None)
            except ImportError:
                # Fallback: just remove timezone (assume already IST)
                candle_time = candle_time.replace(tzinfo=None)
        
        next_candle_start = candle_time + timedelta(minutes=timeframe_minutes)
        
        # Candle is complete if current time >= next candle start time
        return current_time >= next_candle_start
    
    def _get_complete_candles(self, df: pd.DataFrame, timeframe_minutes: int) -> pd.DataFrame:
        """
        Filter DataFrame to include only complete candles.
        Excludes the last candle if it's still forming.
        
        Args:
            df: DataFrame with candles (must have 'Date' column)
            timeframe_minutes: Timeframe in minutes (15 for 15m, 60 for 1h)
        
        Returns:
            DataFrame with only complete candles
        """
        if df.empty:
            return df
        
        # Ensure Date is datetime and timezone-naive
        if not pd.api.types.is_datetime64_any_dtype(df['Date']):
            df['Date'] = pd.to_datetime(df['Date'])
        
        # Normalize Date column to IST-naive if needed (safety check)
        if df['Date'].dt.tz is not None:
            # Convert to IST, then remove timezone info
            df['Date'] = df['Date'].dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
        
        # Check each candle and filter out incomplete ones
        complete_candles = []
        
        for idx, row in df.iterrows():
            candle_time = row['Date']
            if self._is_candle_complete(candle_time, timeframe_minutes):
                complete_candles.append(row)
            else:
                # Once we hit an incomplete candle, stop (remaining are incomplete)
                logger.debug(f"Excluding incomplete candle at {candle_time} ({timeframe_minutes}m timeframe)")
                break
        
        if complete_candles:
            return pd.DataFrame(complete_candles).reset_index(drop=True)
        else:
            return pd.DataFrame(columns=df.columns)
    
    def _rate_limit(self):
        """Ensure rate limiting (1 request per second)."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _fetch_candles_with_retry(
        self,
        params: Dict,
        max_retries: int = MAX_RETRIES,
        retry_delay: int = RETRY_DELAY
    ) -> Optional[Dict]:
        """
        Fetch historical candles with retry logic for resilient API calls.
        Handles AB1004 and other transient errors.
        
        Args:
            params: Parameters for getCandleData API call
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 5)
        
        Returns:
            API response dictionary or None if all retries failed
        """
        for attempt in range(1, max_retries + 1):
            try:
                self._rate_limit()
                
                # Call SmartAPI getCandleData
                response = self.smart_api.getCandleData(params)
                
                # Check if response is valid
                if not isinstance(response, dict):
                    logger.warning(f"[Retry {attempt}/{max_retries}] Historical candles API returned unexpected type: {type(response)}")
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        continue
                    return None
                
                # Check response status
                if response.get('status') == True or response.get('status') is None:
                    # If status is True or None, check if data exists
                    data = response.get('data', [])
                    if data or len(data) > 0:
                        logger.debug(f"Successfully fetched candles on attempt {attempt}")
                        return response
                    else:
                        logger.warning(f"[Retry {attempt}/{max_retries}] Empty or invalid data in response")
                else:
                    error_msg = response.get('message', 'Unknown error')
                    error_code = response.get('errorcode', '')
                    logger.warning(f"[Retry {attempt}/{max_retries}] Historical candles fetch failed: {error_msg} (code: {error_code})")
                    
                    # For AB1004 or other errors, retry with smaller window on last attempt
                    if attempt == max_retries - 1 and error_code in ['AB1004', '']:
                        logger.info("Attempting final retry with smaller date window")
                        # Try with 6-hour window instead of full window
                        smaller_from = (datetime.now() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M")
                        retry_params = params.copy()
                        retry_params['fromdate'] = smaller_from
                        self._rate_limit()
                        retry_resp = self.smart_api.getCandleData(retry_params)
                        if isinstance(retry_resp, dict) and (retry_resp.get('status') == True or retry_resp.get('status') is None):
                            data = retry_resp.get('data', [])
                            if data and len(data) > 0:
                                logger.info(f"Retry with smaller window succeeded on attempt {attempt + 1}")
                                return retry_resp
                
                # If not successful and not last attempt, sleep and retry
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"All {max_retries} retries failed for getCandleData")
                    return None
                    
            except Exception as e:
                logger.error(f"[Retry {attempt}/{max_retries}] Exception occurred: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error("All retries exhausted due to exceptions")
                    return None
        
        return None
    
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
            # This is a workaround if symbol search API doesn't work (expected for some brokers)
            logger.info("NIFTY token not found via search API, using known fallback token (99926000)")
            known_nifty_token = "99926000"  # Known NIFTY 50 index token on NSE
            
            # Verify the token works by trying to fetch market data
            test_ohlc = self.fetch_ohlc(known_nifty_token, self.nifty_exchange)
            if test_ohlc:
                self.nifty_token = known_nifty_token
                self.nifty_tradingsymbol = "NIFTY"
                logger.info(f"Successfully using known NIFTY token: {self.nifty_token}")
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
                # Reuse broker's configured identity headers
                headers = {
                    "Authorization": f"Bearer {self.broker.auth_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-ClientLocalIP": getattr(self.broker, 'local_ip', '192.168.1.5'),
                    "X-ClientPublicIP": getattr(self.broker, 'public_ip', '122.164.104.89'),
                    "X-MACAddress": getattr(self.broker, 'mac_address', 'E8:9C:25:81:DD:AB'),
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
            
            # Default to last 3 days if dates not provided (expanded for reliable resampling)
            if to_date is None:
                to_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if from_date is None:
                # Expand to 3 days to ensure sufficient data for aggregation
                from_datetime = datetime.now() - timedelta(days=3)
                from_date = from_datetime.strftime("%Y-%m-%d %H:%M")
                logger.debug(f"Fetching historical data from {from_date} to {to_date} (3-day window)")
            
            # Format request for getCandleData
            params = {
                "exchange": exchange,
                "symboltoken": symbol_token,
                "interval": interval,
                "fromdate": from_date,
                "todate": to_date
            }
            
            # Call SmartAPI getCandleData with retry logic
            response = self._fetch_candles_with_retry(params)
            
            if response is None:
                logger.error("Failed to fetch historical candles after all retries")
                return None
            
            # Parse response
            # SmartAPI getCandleData may return data in different formats
            data = response.get('data', [])
            
            # If data is not a list, it might be a dict with nested structure
            if isinstance(data, dict):
                # Check for common nested formats
                # Some APIs return: {"data": {"fetched": [...]}}
                # Others return: {"data": [...]} directly
                if 'fetched' in data:
                    data = data.get('fetched', [])
                elif 'data' in data:
                    data = data.get('data', [])
                else:
                    # Try to extract any list from the dict
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            data = value
                            logger.debug(f"Found data in nested key '{key}'")
                            break
                    
                    if not isinstance(data, list):
                        logger.warning(f"Could not extract list from data dict. Keys: {list(data.keys())}")
                        data = []
            
            if not data or len(data) == 0:
                logger.warning(f"No historical candle data returned for interval {interval} from {from_date} to {to_date}")
                logger.debug(f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'N/A'}")
                if isinstance(response.get('data'), dict):
                    logger.debug(f"Response data keys: {list(response.get('data', {}).keys())}")
                    logger.debug(f"Response data content: {str(response.get('data', {}))[:500]}")
                # Log error code and message if available
                if response.get('errorcode'):
                    logger.debug(f"API error code: {response.get('errorcode')}, message: {response.get('message', 'N/A')}")
                # This might be normal if market is closed or no data for the time range
                return None
            
            # Convert to DataFrame
            try:
                # SmartAPI historical data often returns list of lists:
                # [ [timestamp, open, high, low, close, volume], ... ]
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    expected_len = len(data[0])
                    if expected_len >= 5:
                        # Map first 6 columns if available
                        cols = ['datetime', 'open', 'high', 'low', 'close']
                        if expected_len >= 6:
                            cols.append('volume')
                        # Truncate/extend each row to match columns length
                        normalized = [row[:len(cols)] + [None]*(len(cols)-len(row)) for row in data]
                        df = pd.DataFrame(normalized, columns=cols)
                    else:
                        # Fallback to generic DataFrame
                        df = pd.DataFrame(data)
                else:
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
            # SmartAPI getCandleData may return different timestamp formats
            timestamp_found = False
            
            # Try common timestamp column names
            timestamp_columns = ['time', 'datetime', 'date', 'timestamp', 'timestamp_local', 'timestamp_utc', 0]
            for col in timestamp_columns:
                if col in df.columns:
                    try:
                        # Parse timestamp - may be timezone-aware from API
                        parsed_dates = pd.to_datetime(df[col])
                        # Convert timezone-aware datetimes to IST (Indian Standard Time)
                        # Indian market uses IST (UTC+5:30)
                        if parsed_dates.dt.tz is not None:
                            # Convert to IST first, then remove timezone info to make it naive IST
                            parsed_dates = parsed_dates.dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
                        else:
                            # If naive, assume it's already in IST (common for Indian broker APIs)
                            # Log for debugging
                            logger.debug(f"Timestamp is timezone-naive, assuming IST")
                        df['Date'] = parsed_dates
                        timestamp_found = True
                        logger.debug(f"Using '{col}' column as timestamp (converted to IST)")
                        break
                    except Exception as e:
                        logger.debug(f"Failed to parse '{col}' as timestamp: {e}")
                        continue
            
            # If no timestamp column found, check if first column is datetime-like
            if not timestamp_found and len(df.columns) > 0:
                first_col = df.columns[0]
                try:
                    parsed_dates = pd.to_datetime(df[first_col])
                    # Normalize timezone-aware to IST
                    if parsed_dates.dt.tz is not None:
                        # Convert to IST, then remove timezone info
                        parsed_dates = parsed_dates.dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
                    else:
                        logger.debug(f"First column timestamp is timezone-naive, assuming IST")
                    df['Date'] = parsed_dates
                    timestamp_found = True
                    logger.debug(f"Using first column '{first_col}' as timestamp (IST)")
                except Exception:
                    pass
            
            if not timestamp_found:
                logger.warning(f"No timestamp column found in historical data. Available columns: {list(df.columns)}")
                logger.debug(f"Data sample: {df.head(2) if not df.empty else 'Empty DataFrame'}")
                # Try to use index as timestamp if it's datetime
                if isinstance(df.index, pd.DatetimeIndex):
                    index_dates = df.index
                    # Normalize timezone-aware to IST
                    if index_dates.tz is not None:
                        # Convert to IST, then remove timezone info
                        index_dates = index_dates.tz_convert('Asia/Kolkata').tz_localize(None)
                    else:
                        logger.debug("Index timestamp is timezone-naive, assuming IST")
                    df['Date'] = index_dates
                    timestamp_found = True
                    logger.debug("Using DataFrame index as timestamp (IST)")
                else:
                    return None
            
            # Ensure we have OHLC columns
            column_mapping = {
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume',
                1: 'Open',
                2: 'High',
                3: 'Low',
                4: 'Close',
                5: 'Volume'
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
            
            # Log successful fetch with details
            if len(df) > 0:
                logger.info(f"Fetched {len(df)} historical candles from {from_date} to {to_date} (interval: {interval})")
                logger.debug(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
            else:
                logger.warning(f"No candles returned for interval {interval} from {from_date} to {to_date}")
            
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
        
        # Drop duplicates by Date (keep first occurrence)
        raw_data = raw_data.drop_duplicates(subset=['Date'], keep='first')
        
        # Drop rows with NaN values before resampling
        raw_data = raw_data.dropna(subset=['Open', 'High', 'Low', 'Close'])
        
        if raw_data.empty:
            logger.warning("No valid 1-minute candles after dropping NaNs/duplicates")
            return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        
        # Set Date as index for resampling
        df = raw_data.set_index('Date').copy()
        
        # Resample to 15 minutes
        aggregated = df.resample('15min').agg({
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
        
        # Drop duplicates by Date (keep first occurrence)
        raw_data = raw_data.drop_duplicates(subset=['Date'], keep='first')
        
        # Drop rows with NaN values before resampling
        raw_data = raw_data.dropna(subset=['Open', 'High', 'Low', 'Close'])
        
        if raw_data.empty:
            logger.warning("No valid 1-minute candles after dropping NaNs/duplicates for 1H aggregation")
            return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        
        # Set Date as index for resampling
        df = raw_data.set_index('Date').copy()
        
        # Resample to 1 hour
        aggregated = df.resample('1h').agg({
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
    
    def get_1h_data(self, window_hours: int = 48, use_direct_interval: bool = True) -> pd.DataFrame:
        """
        Get 1-hour aggregated data.
        Tries direct ONE_HOUR interval first, falls back to resampling from ONE_MINUTE if needed.
        
        Args:
            window_hours: Number of hours of data to return (default: 48)
            use_direct_interval: If True, try fetching ONE_HOUR directly first (default: True)
        
        Returns:
            DataFrame with 1-hour OHLC candles
        """
        # IMPORTANT: Request data up to 5 minutes ago to avoid API delay issues
        current_time = datetime.now()
        to_time = current_time - timedelta(minutes=5)
        from_time = current_time - timedelta(hours=window_hours + 12)  # Add buffer for complete candles
        
        # Try direct ONE_HOUR interval first (more efficient)
        if use_direct_interval:
            hist_data_direct = self.get_historical_candles(
                interval="ONE_HOUR",
                from_date=from_time.strftime("%Y-%m-%d %H:%M"),
                to_date=to_time.strftime("%Y-%m-%d %H:%M")
            )
            
            if hist_data_direct is not None and not hist_data_direct.empty:
                logger.info(f"Successfully fetched {len(hist_data_direct)} 1-hour candles directly")
                self._data_1h = hist_data_direct
                # Trim to requested window (keep most recent)
                if len(self._data_1h) > window_hours:
                    self._data_1h = self._data_1h.tail(window_hours).copy()
                    logger.debug(f"Trimmed to {window_hours} most recent 1-hour candles")
                
                # Exclude incomplete candles and return
                all_candles = self._data_1h.copy()
                complete_candles = self._get_complete_candles(all_candles, timeframe_minutes=60)
                if len(complete_candles) < len(all_candles):
                    excluded_count = len(all_candles) - len(complete_candles)
                    logger.info(f"Excluded {excluded_count} incomplete 1-hour candle(s) from strategy data")
                if complete_candles.empty:
                    logger.warning("No complete 1-hour candles available after filtering")
                return complete_candles
            else:
                logger.info("Direct ONE_HOUR fetch failed or returned empty, falling back to resampling from ONE_MINUTE")
        
        # Fallback: Fetch 1-minute data and resample
        fetch_window_days = 3
        hist_data = self.get_historical_candles(
            interval="ONE_MINUTE",
            from_date=(current_time - timedelta(days=fetch_window_days)).strftime("%Y-%m-%d %H:%M"),
            to_date=to_time.strftime("%Y-%m-%d %H:%M")
        )
        
        if hist_data is not None and not hist_data.empty:
            logger.info(f"Fetched {len(hist_data)} 1-minute candles for 1-hour aggregation")
            
            # Check if we have minimum required candles (need at least ~60 for 1 hour of data)
            if len(hist_data) < 60:
                logger.warning(f"Insufficient 1-minute data ({len(hist_data)} candles). Need at least 60 candles. Data may be too recent or unavailable.")
                return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            
            # Aggregate to 1-hour
            self._data_1h = self._aggregate_to_1h(hist_data)
            
            logger.info(f"Aggregated to {len(self._data_1h)} 1-hour candles")
            
            # Trim to requested window (keep most recent)
            if len(self._data_1h) > window_hours:
                self._data_1h = self._data_1h.tail(window_hours).copy()
                logger.debug(f"Trimmed to {window_hours} most recent 1-hour candles")
        else:
            logger.warning("No historical 1-minute data available for 1-hour aggregation. Data may be too recent or API unavailable.")
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
        
        # Get all candles and filter to complete ones only
        all_candles = self._data_1h.tail(window_hours).copy() if not self._data_1h.empty else pd.DataFrame(
            columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        )
        
        # Exclude incomplete candles (1-hour timeframe = 60 minutes)
        complete_candles = self._get_complete_candles(all_candles, timeframe_minutes=60)
        
        if len(complete_candles) < len(all_candles):
            excluded_count = len(all_candles) - len(complete_candles)
            logger.info(f"Excluded {excluded_count} incomplete 1-hour candle(s) from strategy data")
        
        if complete_candles.empty:
            logger.warning("No complete 1-hour candles available after filtering")
        
        return complete_candles
    
    def get_15m_data(self, window_hours: int = 12, use_direct_interval: bool = True) -> pd.DataFrame:
        """
        Get 15-minute aggregated data.
        Tries direct FIFTEEN_MINUTE interval first, falls back to resampling from ONE_MINUTE if needed.
        
        Args:
            window_hours: Number of hours of data to return (default: 12)
            use_direct_interval: If True, try fetching FIFTEEN_MINUTE directly first (default: True)
        
        Returns:
            DataFrame with 15-minute OHLC candles
        """
        # IMPORTANT: Request data up to 5 minutes ago to avoid API delay issues
        current_time = datetime.now()
        to_time = current_time - timedelta(minutes=5)
        from_time = current_time - timedelta(hours=window_hours + 2)  # Add buffer for complete candles
        
        # Try direct FIFTEEN_MINUTE interval first (more efficient)
        if use_direct_interval:
            hist_data_direct = self.get_historical_candles(
                interval="FIFTEEN_MINUTE",
                from_date=from_time.strftime("%Y-%m-%d %H:%M"),
                to_date=to_time.strftime("%Y-%m-%d %H:%M")
            )
            
            if hist_data_direct is not None and not hist_data_direct.empty:
                logger.info(f"Successfully fetched {len(hist_data_direct)} 15-minute candles directly")
                self._data_15m = hist_data_direct
                # Trim to requested window (keep most recent)
                max_candles = (window_hours * 60) // 15
                if len(self._data_15m) > max_candles:
                    self._data_15m = self._data_15m.tail(max_candles).copy()
                    logger.debug(f"Trimmed to {max_candles} most recent 15-minute candles")
                
                # Exclude incomplete candles and return
                all_candles = self._data_15m.copy()
                complete_candles = self._get_complete_candles(all_candles, timeframe_minutes=15)
                if len(complete_candles) < len(all_candles):
                    excluded_count = len(all_candles) - len(complete_candles)
                    logger.info(f"Excluded {excluded_count} incomplete 15-minute candle(s) from strategy data")
                if complete_candles.empty:
                    logger.warning("No complete 15-minute candles available after filtering. Consider waiting 5-10 minutes for new candles to form.")
                return complete_candles
            else:
                logger.info("Direct FIFTEEN_MINUTE fetch failed or returned empty, falling back to resampling from ONE_MINUTE")
        
        # Fallback: Fetch 1-minute data and resample
        fetch_window_days = 3
        hist_data = self.get_historical_candles(
            interval="ONE_MINUTE",
            from_date=(current_time - timedelta(days=fetch_window_days)).strftime("%Y-%m-%d %H:%M"),
            to_date=to_time.strftime("%Y-%m-%d %H:%M")
        )
        
        if hist_data is not None and not hist_data.empty:
            logger.info(f"Fetched {len(hist_data)} 1-minute candles for 15-minute aggregation")
            
            # Check if we have minimum required candles (need at least ~60 for 15 hours of 15m data)
            if len(hist_data) < 60:
                logger.warning(f"Insufficient 1-minute data ({len(hist_data)} candles). Need at least 60 candles. Data may be too recent or unavailable.")
                return pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            
            # Aggregate to 15-minute
            self._data_15m = self._aggregate_to_15m(hist_data)
            
            logger.info(f"Aggregated to {len(self._data_15m)} 15-minute candles")
            
            # Trim to requested window (keep most recent)
            max_candles = (window_hours * 60) // 15
            if len(self._data_15m) > max_candles:
                self._data_15m = self._data_15m.tail(max_candles).copy()
                logger.debug(f"Trimmed to {max_candles} most recent 15-minute candles")
        else:
            logger.warning("No historical 1-minute data available for 15-minute aggregation. Data may be too recent or API unavailable.")
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
        
        # Get all candles and filter to complete ones only
        max_candles = (window_hours * 60) // 15
        all_candles = self._data_15m.tail(max_candles).copy() if not self._data_15m.empty else pd.DataFrame(
            columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        )
        
        # Exclude incomplete candles (15-minute timeframe)
        complete_candles = self._get_complete_candles(all_candles, timeframe_minutes=15)
        
        if len(complete_candles) < len(all_candles):
            excluded_count = len(all_candles) - len(complete_candles)
            logger.info(f"Excluded {excluded_count} incomplete 15-minute candle(s) from strategy data")
        
        if complete_candles.empty:
            logger.warning("No complete 15-minute candles available after filtering. Consider waiting 5-10 minutes for new candles to form.")
        
        return complete_candles
    
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
                
                # Note: Historical data aggregation may include the current incomplete candle
                # This will be filtered out when get_15m_data() or get_1h_data() is called
                logger.debug("Aggregated from historical data - incomplete candles will be filtered in get methods")
            else:
                # Fallback: Update with current snapshot
                # Only create new candle if period has changed (new candle started)
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
                else:
                    # Update existing incomplete candle
                    last_idx = len(self._data_15m) - 1
                    self._data_15m.loc[last_idx, 'High'] = max(self._data_15m.loc[last_idx, 'High'], ohlc.get('high', 0))
                    self._data_15m.loc[last_idx, 'Low'] = min(self._data_15m.loc[last_idx, 'Low'], ohlc.get('low', 0))
                    self._data_15m.loc[last_idx, 'Close'] = ohlc.get('ltp', ohlc.get('close', 0))
                    self._data_15m.loc[last_idx, 'Volume'] = ohlc.get('tradeVolume', 0)
                
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
                else:
                    # Update existing incomplete candle
                    last_idx = len(self._data_1h) - 1
                    self._data_1h.loc[last_idx, 'High'] = max(self._data_1h.loc[last_idx, 'High'], ohlc.get('high', 0))
                    self._data_1h.loc[last_idx, 'Low'] = min(self._data_1h.loc[last_idx, 'Low'], ohlc.get('low', 0))
                    self._data_1h.loc[last_idx, 'Close'] = ohlc.get('ltp', ohlc.get('close', 0))
                    self._data_1h.loc[last_idx, 'Volume'] = ohlc.get('tradeVolume', 0)
            
            logger.info("Market data refreshed successfully")
    
    def get_candle_status(self, timeframe: str = "15m") -> Dict:
        """
        Get status of current candle (complete or incomplete).
        
        Args:
            timeframe: "15m" or "1h"
        
        Returns:
            Dictionary with candle status information:
            {
                'current_candle_time': datetime,
                'is_complete': bool,
                'next_candle_start': datetime,
                'time_remaining_minutes': float
            }
        """
        current_time = datetime.now()
        
        if timeframe == "15m":
            rounded_time = current_time.replace(minute=(current_time.minute // 15) * 15, second=0, microsecond=0)
            timeframe_minutes = 15
        elif timeframe == "1h":
            rounded_time = current_time.replace(minute=0, second=0, microsecond=0)
            timeframe_minutes = 60
        else:
            return {
                'error': f"Invalid timeframe: {timeframe}. Use '15m' or '1h'"
            }
        
        next_candle_start = rounded_time + timedelta(minutes=timeframe_minutes)
        is_complete = self._is_candle_complete(rounded_time, timeframe_minutes)
        time_remaining = (next_candle_start - current_time).total_seconds() / 60.0 if not is_complete else 0.0
        
        return {
            'current_candle_time': rounded_time,
            'is_complete': is_complete,
            'next_candle_start': next_candle_start,
            'time_remaining_minutes': max(0.0, time_remaining),
            'timeframe': timeframe
        }

