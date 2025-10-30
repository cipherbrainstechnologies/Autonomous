"""
Broker Connector for abstract broker interface
Supports multiple broker APIs (Angel One, Fyers)
"""

from typing import Dict, Optional, List
from abc import ABC, abstractmethod
import pyotp
from logzero import logger
try:
    from SmartApi.smartConnect import SmartConnect
except ImportError:
    # Fallback if smartapi-python is not installed
    SmartConnect = None


class BrokerInterface(ABC):
    """
    Abstract base class for broker interfaces.
    """
    
    @abstractmethod
    def place_order(
        self,
        symbol: str,
        strike: int,
        direction: str,
        quantity: int,
        order_type: str = "MARKET",
        price: Optional[float] = None
    ) -> Dict:
        """
        Place an order with the broker.
        
        Args:
            symbol: Trading symbol (e.g., 'NIFTY')
            strike: Strike price
            direction: 'CE' for Call, 'PE' for Put
            quantity: Number of lots
            order_type: 'MARKET' or 'LIMIT'
            price: Limit price (required for LIMIT orders)
        
        Returns:
            Dictionary with order details including 'order_id'
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """
        Get current open positions.
        
        Returns:
            List of position dictionaries
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Broker order ID
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict:
        """
        Get order status.
        
        Args:
            order_id: Broker order ID
        
        Returns:
            Dictionary with order status information
        """
        pass
    
    @abstractmethod
    def modify_order(
        self,
        order_id: str,
        price: Optional[float] = None,
        quantity: Optional[int] = None
    ) -> bool:
        """
        Modify an existing order.
        
        Args:
            order_id: Broker order ID
            price: New price (for LIMIT orders)
            quantity: New quantity
        
        Returns:
            True if successful, False otherwise
        """
        pass


class AngelOneBroker(BrokerInterface):
    """
    Angel One SmartAPI broker implementation.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Angel One broker connection.
        
        Args:
            config: Configuration dictionary with broker credentials
        """
        if SmartConnect is None:
            raise ImportError(
                "smartapi-python not installed. Install with: pip install smartapi-python"
            )
        
        self.api_key = config.get('api_key', '')
        self.username = config.get('username', config.get('client_id', ''))
        self.pwd = config.get('pwd', '')
        self.token = config.get('token', '')  # TOTP QR secret
        self.client_id = config.get('client_id', '')
        # Network identity headers for WAF compliance
        self.local_ip = config.get('local_ip', '192.168.1.5')
        self.public_ip = config.get('public_ip', '122.164.104.89')
        self.mac_address = config.get('mac', 'E8:9C:25:81:DD:AB')
        
        # Initialize SmartConnect
        self.smart_api = SmartConnect(self.api_key)
        
        # Session tokens (lazy initialization)
        self.auth_token = None
        self.refresh_token = None
        self.feed_token = None
        self.session_generated = False
        
        logger.info("AngelOneBroker initialized. Session will be generated on first API call.")

    def _default_headers(self) -> Dict:
        """
        Build default headers for direct REST calls (symbol search, market quote, greeks).
        """
        return {
            "Authorization": f"Bearer {self.auth_token}" if self.auth_token else "",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": self.local_ip,
            "X-ClientPublicIP": self.public_ip,
            "X-MACAddress": self.mac_address,
            "X-PrivateKey": self.api_key
        }
    
    def _generate_session(self) -> bool:
        """
        Generate SmartAPI session using TOTP authentication.
        
        Returns:
            True if session generated successfully, False otherwise
        """
        try:
            if not self.token:
                logger.error("TOTP token not configured in secrets.toml")
                return False
            
            # Generate TOTP
            totp = pyotp.TOTP(self.token).now()
            logger.info(f"Generated TOTP for session (username: {self.username})")
            
            # Generate session
            data = self.smart_api.generateSession(self.username, self.pwd, totp)
            
            if data.get('status') == False:
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"Session generation failed: {error_msg}")
                return False
            
            # Store tokens
            response_data = data.get('data', {})
            self.auth_token = response_data.get('jwtToken')
            self.refresh_token = response_data.get('refreshToken')
            
            # Get feed token
            self._get_feed_token()
            
            self.session_generated = True
            logger.info("SmartAPI session generated successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Error generating session: {e}")
            return False
    
    def _refresh_token(self) -> bool:
        """
        Refresh SmartAPI session token using refresh token.
        
        Returns:
            True if token refreshed successfully, False otherwise
        """
        try:
            if not self.refresh_token:
                logger.warning("No refresh token available. Generating new session...")
                return self._generate_session()
            
            # Generate new token using refresh token
            token_data = self.smart_api.generateToken(self.refresh_token)
            
            if token_data.get('status') == False:
                logger.warning("Token refresh failed. Generating new session...")
                return self._generate_session()
            
            response_data = token_data.get('data', {})
            self.auth_token = response_data.get('jwtToken', self.auth_token)
            logger.info("Token refreshed successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Error refreshing token: {e}")
            # Try generating new session
            return self._generate_session()
    
    def _get_feed_token(self) -> bool:
        """
        Get feed token for market data.
        
        Returns:
            True if feed token retrieved successfully, False otherwise
        """
        try:
            feed_token_data = self.smart_api.getfeedToken()
            
            # Handle case where response might be a string or unexpected format
            if isinstance(feed_token_data, str):
                logger.error(f"Feed token API returned string instead of dict: {feed_token_data[:100]}")
                return False
            
            if not isinstance(feed_token_data, dict):
                logger.error(f"Feed token API returned unexpected type: {type(feed_token_data)}")
                return False
            
            if feed_token_data.get('status') == False:
                logger.error(f"Failed to get feed token: {feed_token_data.get('message')}")
                return False
            
            response_data = feed_token_data.get('data', {})
            self.feed_token = response_data.get('feedToken')
            
            if self.feed_token:
                logger.info("Feed token retrieved successfully")
                return True
            else:
                logger.warning("Feed token not found in response")
                return False
            
        except Exception as e:
            logger.exception(f"Error getting feed token: {e}")
            return False
    
    def _ensure_session(self) -> bool:
        """
        Ensure valid session exists. Generates or refreshes if needed.
        
        Returns:
            True if valid session exists, False otherwise
        """
        if not self.session_generated:
            return self._generate_session()
        
        # Check if token is still valid by trying to refresh
        # If refresh fails, generate new session
        return self._refresh_token()
    
    def _search_symbol(self, exchange: str, symbol: str) -> Optional[Dict]:
        """
        Search for symbol using SmartAPI Symbol Search API.
        Uses direct REST API call since SmartAPI-Python doesn't have symbolSearch method.
        
        Args:
            exchange: Exchange code (NSE, NFO, BSE, etc.)
            symbol: Symbol name to search (e.g., "NIFTY", "SBIN")
        
        Returns:
            API response dictionary or None if error
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot search symbol: No valid session")
                return None
            
            if not self.auth_token:
                logger.error("Auth token not available for symbol search")
                return None
            
            # SmartAPI Symbol Search API endpoint
            url = "https://apiconnect.angelone.in/rest/secure/angelbroking/market/v1/searchscrip"
            headers = self._default_headers()
            
            # Request format based on SmartAPI pattern
            request_params = {
                "searchscrip": symbol,
                "exchange": exchange
            }
            
            import requests
            response = requests.post(url, json=request_params, headers=headers, timeout=10)
            
            # Check response status code
            if response.status_code != 200:
                logger.error(f"Symbol search API returned status code {response.status_code}: {response.text[:200]}")
                return None
            
            # Check if response is JSON
            content_type = response.headers.get('content-type', '').lower()
            if 'application/json' not in content_type:
                logger.error(f"Symbol search API returned non-JSON response (content-type: {content_type}): {response.text[:200]}")
                return None
            
            # Try to parse JSON
            try:
                response_data = response.json()
            except ValueError as json_error:
                logger.error(f"Failed to parse JSON response: {json_error}")
                logger.debug(f"Response text: {response.text[:500]}")
                return None
            
            if not isinstance(response_data, dict):
                logger.error(f"Symbol search API returned unexpected response type: {type(response_data)}")
                return None
            
            if response_data.get('status') == False or response_data.get('success') == False:
                error_msg = response_data.get('message', 'Unknown error')
                logger.error(f"Symbol search failed: {error_msg}")
                return None
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.exception(f"Network error searching symbol {symbol} on {exchange}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Error searching symbol {symbol} on {exchange}: {e}")
            return None
    
    def _get_symbol_token(self, tradingsymbol: str, exchange: str = "NFO") -> Optional[str]:
        """
        Fetch symboltoken from SmartAPI symbol master.
        
        Args:
            tradingsymbol: Trading symbol (e.g., "NIFTY29OCT2419000CE")
            exchange: Exchange code (default: "NFO" for options)
        
        Returns:
            Symbol token string if found, None otherwise
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch symbol token: No valid session")
                return None
            
            # Search for symbol using direct API call
            symbol_result = self._search_symbol(exchange, tradingsymbol)
            
            if not symbol_result:
                logger.error(f"Symbol lookup failed for {tradingsymbol}")
                return None
            
            # Parse response - check different possible response formats
            symbols = symbol_result.get('data', [])
            if not symbols:
                # Try alternative response format
                symbols = symbol_result.get('fetched', [])
            
            if not symbols:
                logger.warning(f"Symbol {tradingsymbol} not found in symbol master")
                return None
            
            # Return first match's symboltoken
            symbol_token = symbols[0].get('symboltoken')
            logger.info(f"Found symbol token for {tradingsymbol}: {symbol_token}")
            return symbol_token
            
        except Exception as e:
            logger.exception(f"Error fetching symbol token for {tradingsymbol}: {e}")
            return None
    
    def _format_option_symbol(self, symbol: str, strike: int, direction: str, expiry_date: Optional[str] = None) -> str:
        """
        Format NIFTY option symbol for SmartAPI.
        
        Format: NIFTY{DD}{MON}{YY}{STRIKE}{CE/PE}
        Example: NIFTY29OCT2419000CE
        
        Args:
            symbol: Base symbol (e.g., "NIFTY")
            strike: Strike price
            direction: "CE" or "PE"
            expiry_date: Optional expiry date in format "29OCT24". If not provided, 
                       will need to be determined from current date and nearest expiry
        
        Returns:
            Formatted trading symbol
        """
        # Determine current expiry date if not provided (weekly expiry every Tuesday)
        if expiry_date is None:
            expiry_date = self._get_next_tuesday_expiry_ddmmmyy()
        
        return f"{symbol}{expiry_date}{strike}{direction}"

    def _get_next_tuesday_expiry_ddmmmyy(self) -> str:
        """
        Calculate next Tuesday from today and return in DDMMMYY (e.g., 29OCT24).
        If today is Tuesday before market close, use today.
        """
        from datetime import datetime, timedelta
        now = datetime.now()
        weekday = now.weekday()  # Monday=0 ... Sunday=6
        # Tuesday is 1
        days_ahead = (1 - weekday) % 7
        # If today is Tuesday and time is after market close (15:30), move to next Tuesday
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        if days_ahead == 0 and now > market_close:
            days_ahead = 7
        next_tuesday = now + timedelta(days=days_ahead)
        return next_tuesday.strftime('%d%b%y').upper()

    def _get_next_tuesday_expiry_ddmmmyyyy(self) -> str:
        """
        Calculate next Tuesday from today and return in DDMMMYYYY (e.g., 29OCT2024) for APIs like optionGreek.
        """
        from datetime import datetime, timedelta
        now = datetime.now()
        weekday = now.weekday()
        days_ahead = (1 - weekday) % 7
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        if days_ahead == 0 and now > market_close:
            days_ahead = 7
        next_tuesday = now + timedelta(days=days_ahead)
        return next_tuesday.strftime('%d%b%Y').upper()

    def get_option_greeks(self, underlying: str, expiry_date: Optional[str] = None) -> List[Dict]:
        """
        Fetch option Greeks (Delta, Gamma, Theta, Vega, IV) for an underlying & expiry.
        Uses SmartAPI endpoint: /rest/secure/angelbroking/marketData/v1/optionGreek
        Request body: {"name": "NIFTY", "expirydate": "25JAN2024"}
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch option Greeks: No valid session")
                return []
            if not self.auth_token:
                logger.error("Auth token not available for option Greeks API")
                return []
            # Expiry date format for API is DDMMMYYYY
            if expiry_date is None:
                expiry_date = self._get_next_tuesday_expiry_ddmmmyyyy()
            import requests
            url = "https://apiconnect.angelone.in/rest/secure/angelbroking/marketData/v1/optionGreek"
            headers = self._default_headers()
            payload = {"name": underlying, "expirydate": expiry_date}
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Option Greeks API status {resp.status_code}: {resp.text[:200]}")
                return []
            ctype = resp.headers.get('content-type', '').lower()
            if 'application/json' not in ctype:
                logger.error(f"Option Greeks API non-JSON response: {ctype}")
                return []
            data = resp.json()
            if not isinstance(data, dict) or data.get('status') is False:
                logger.error(f"Option Greeks API error: {data.get('message') if isinstance(data, dict) else 'Unknown'}")
                return []
            greeks = data.get('data', []) or []
            logger.info(f"Fetched {len(greeks)} option Greek rows for {underlying} {expiry_date}")
            return greeks
        except Exception as e:
            logger.exception(f"Error fetching option Greeks: {e}")
            return []
    
    def place_order(
        self,
        symbol: str,
        strike: int,
        direction: str,
        quantity: int,
        order_type: str = "MARKET",
        price: Optional[float] = None
    ) -> Dict:
        """
        Place order via Angel One SmartAPI.
        
        Args:
            symbol: Trading symbol (e.g., 'NIFTY')
            strike: Strike price
            direction: 'CE' for Call, 'PE' for Put
            quantity: Number of lots (will be multiplied by lot size)
            order_type: 'MARKET' or 'LIMIT'
            price: Limit price (required for LIMIT orders)
        
        Returns:
            Dictionary with order details including 'order_id' and 'status'
        """
        try:
            # Ensure valid session
            if not self._ensure_session():
                return {
                    "status": False,
                    "message": "Failed to establish broker session",
                    "order_id": None
                }
            
            # Format trading symbol
            tradingsymbol = self._format_option_symbol(symbol, strike, direction)
            
            # Get symbol token
            symboltoken = self._get_symbol_token(tradingsymbol, "NFO")
            
            if not symboltoken:
                return {
                    "status": False,
                    "message": f"Symbol {tradingsymbol} not found in symbol master",
                    "order_id": None
                }
            
            # Build order parameters
            orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": tradingsymbol,
                "symboltoken": symboltoken,
                "transactiontype": "BUY",
                "exchange": "NFO",
                "ordertype": order_type,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": str(price) if order_type == "LIMIT" and price else "0",
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(quantity)
            }
            
            logger.info(f"Placing order: {orderparams}")
            
            # Place order - use placeOrderFullResponse for detailed error info
            response = self.smart_api.placeOrderFullResponse(orderparams)
            
            if response.get('status') == False:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"Order placement failed: {error_msg}")
                return {
                    "status": False,
                    "message": f"Order rejected: {error_msg}",
                    "order_id": None,
                    "order_data": orderparams
                }
            
            # Extract order ID from response
            response_data = response.get('data', {})
            order_id = response_data.get('orderid') or response_data.get('orderId')
            
            logger.info(f"Order placed successfully. Order ID: {order_id}")
            
            return {
                "status": True,
                "message": "Order placed successfully",
                "order_id": str(order_id) if order_id else None,
                "order_data": orderparams,
                "symboltoken": symboltoken,
                "exchange": "NFO",
                "response": response_data
            }
            
        except Exception as e:
            logger.exception(f"Error placing order: {e}")
            return {
                "status": False,
                "message": f"Order placement error: {str(e)}",
                "order_id": None
            }
    
    def get_positions(self) -> List[Dict]:
        """
        Get current positions from Angel One.
        
        Returns:
            List of position dictionaries
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch positions: No valid session")
                return []
            
            position_response = self.smart_api.position()
            
            if position_response.get('status') == False:
                logger.error(f"Failed to fetch positions: {position_response.get('message')}")
                return []
            
            positions = position_response.get('data', [])
            logger.info(f"Retrieved {len(positions)} positions")
            
            return positions
            
        except Exception as e:
            logger.exception(f"Error fetching positions: {e}")
            return []
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel order via Angel One.
        
        Args:
            order_id: Broker order ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot cancel order: No valid session")
                return False
            
            # SmartAPI cancelOrder format
            cancel_params = {
                "variety": "NORMAL",
                "orderid": order_id
            }
            
            response = self.smart_api.cancelOrder(cancel_params)
            
            if response.get('status') == False:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"Order cancellation failed: {error_msg}")
                return False
            
            logger.info(f"Order {order_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Dict:
        """
        Get order status from Angel One.
        
        Args:
            order_id: Broker order ID
        
        Returns:
            Dictionary with order status information
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch order status: No valid session")
                return {"status": "ERROR", "message": "No valid session", "order_id": order_id}
            
            # Fetch order book
            order_book = self.smart_api.orderBook()
            
            if order_book.get('status') == False:
                logger.error(f"Failed to fetch order book: {order_book.get('message')}")
                return {"status": "ERROR", "message": "Failed to fetch order book", "order_id": order_id}
            
            # Find order in order book
            orders = order_book.get('data', [])
            
            for order in orders:
                if str(order.get('orderid')) == str(order_id):
                    logger.info(f"Found order {order_id}: {order.get('status')}")
                    return {
                        "status": order.get('status', 'UNKNOWN'),
                        "order_id": order_id,
                        "order_data": order
                    }
            
            logger.warning(f"Order {order_id} not found in order book")
            return {"status": "NOT_FOUND", "order_id": order_id}
            
        except Exception as e:
            logger.exception(f"Error fetching order status for {order_id}: {e}")
            return {"status": "ERROR", "message": str(e), "order_id": order_id}
    
    def modify_order(
        self,
        order_id: str,
        price: Optional[float] = None,
        quantity: Optional[int] = None
    ) -> bool:
        """
        Modify order via Angel One.
        
        Args:
            order_id: Broker order ID
            price: New price (for LIMIT orders)
            quantity: New quantity
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot modify order: No valid session")
                return False
            
            # First get current order details
            order_status = self.get_order_status(order_id)
            
            if order_status.get('status') == 'NOT_FOUND' or order_status.get('status') == 'ERROR':
                logger.error(f"Cannot modify order {order_id}: Order not found or error occurred")
                return False
            
            order_data = order_status.get('order_data', {})
            
            # Build modify parameters
            modify_params = {
                "variety": order_data.get('variety', 'NORMAL'),
                "orderid": order_id,
                "ordertype": order_data.get('ordertype', 'LIMIT'),
                "producttype": order_data.get('producttype', 'INTRADAY'),
                "duration": order_data.get('duration', 'DAY'),
                "price": str(price) if price else order_data.get('price', '0'),
                "quantity": str(quantity) if quantity else order_data.get('quantity', '0'),
                "tradingsymbol": order_data.get('tradingsymbol', ''),
                "symboltoken": order_data.get('symboltoken', ''),
                "exchange": order_data.get('exchange', 'NFO')
            }
            
            response = self.smart_api.modifyOrder(modify_params)
            
            if response.get('status') == False:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"Order modification failed: {error_msg}")
                return False
            
            logger.info(f"Order {order_id} modified successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Error modifying order {order_id}: {e}")
            return False
    
    def refresh_session(self) -> bool:
        """
        Public method to manually refresh broker session.
        Can be called from dashboard UI.
        
        Returns:
            True if session refreshed successfully, False otherwise
        """
        logger.info("Manual session refresh requested")
        return self._refresh_token()
    
    def get_market_quote(self, params: Dict) -> Dict:
        """
        Get market quote using SmartAPI Market Data API.
        Wrapper for SmartAPI Market Data API.
        
        Args:
            params: Request parameters in format:
                {
                    "mode": "LTP" | "OHLC" | "FULL",
                    "exchangeTokens": {
                        "NSE": ["token1", "token2"],
                        "NFO": ["token3"]
                    }
                }
        
        Returns:
            Dictionary with API response
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch market quote: No valid session")
                return {"status": False, "message": "No valid session"}
            
            # Try using SmartAPI's marketQuote method if available
            try:
                response = self.smart_api.marketQuote(params)
                return response
            except AttributeError:
                # Method doesn't exist, use direct API call
                import requests
                
                if not self.auth_token:
                    logger.error("Auth token not available for market quote API")
                    return {"status": False, "message": "No auth token"}
                
                url = "https://apiconnect.angelone.in/rest/secure/angelbroking/market/v1/quote/"
            headers = self._default_headers()
                
                response = requests.post(url, json=params, headers=headers)
                return response.json()
                
        except Exception as e:
            logger.exception(f"Error fetching market quote: {e}")
            return {"status": False, "message": str(e)}
    
    def get_historical_candles(self, params: Dict) -> Dict:
        """
        Get historical candle data using SmartAPI getCandleData API.
        
        Args:
            params: Request parameters in format:
                {
                    "exchange": "NSE" | "NFO" | "BSE",
                    "symboltoken": "token_string",
                    "interval": "ONE_MINUTE" | "FIVE_MINUTE" | "FIFTEEN_MINUTE" | "THIRTY_MINUTE" | "ONE_HOUR",
                    "fromdate": "YYYY-MM-DD HH:mm",
                    "todate": "YYYY-MM-DD HH:mm"
                }
        
        Returns:
            Dictionary with API response containing historical candle data
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch historical candles: No valid session")
                return {"status": False, "message": "No valid session"}
            
            # Call SmartAPI getCandleData
            response = self.smart_api.getCandleData(params)
            
            if response.get('status') == False:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"Historical candles fetch failed: {error_msg}")
            
            return response
            
        except Exception as e:
            logger.exception(f"Error fetching historical candles: {e}")
            return {"status": False, "message": str(e)}

    def get_holdings(self) -> List[Dict]:
        """
        Fetch current holdings using SmartAPI portfolio endpoint.

        Returns:
            List of holding dictionaries (empty list on error)
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch holdings: No valid session")
                return []
            if not self.auth_token:
                logger.error("Auth token not available for holdings API")
                return []
            import requests
            url = "https://apiconnect.angelone.in/rest/secure/angelbroking/portfolio/v1/getHolding"
            headers = self._default_headers()
            resp = requests.post(url, json={}, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Holdings API status {resp.status_code}: {resp.text[:200]}")
                return []
            ctype = resp.headers.get('content-type', '').lower()
            if 'application/json' not in ctype:
                logger.error(f"Holdings API non-JSON response: {ctype}")
                return []
            data = resp.json()
            if not isinstance(data, dict) or data.get('status') is False:
                logger.error(f"Holdings API error: {data.get('message') if isinstance(data, dict) else 'Unknown'}")
                return []
            holdings = data.get('data', []) or []
            logger.info(f"Fetched {len(holdings)} holdings")
            return holdings
        except Exception as e:
            logger.exception(f"Error fetching holdings: {e}")
            return []

    def get_all_holdings(self) -> Dict:
        """
        Fetch all holdings summary (totals/P&L) using SmartAPI endpoint.

        Returns:
            Dict with totals and holdings data (empty dict on error)
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch all holdings: No valid session")
                return {}
            if not self.auth_token:
                logger.error("Auth token not available for all holdings API")
                return {}
            import requests
            url = "https://apiconnect.angelone.in/rest/secure/angelbroking/portfolio/v1/getAllHolding"
            headers = self._default_headers()
            resp = requests.post(url, json={}, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.error(f"AllHoldings API status {resp.status_code}: {resp.text[:200]}")
                return {}
            ctype = resp.headers.get('content-type', '').lower()
            if 'application/json' not in ctype:
                logger.error(f"AllHoldings API non-JSON response: {ctype}")
                return {}
            data = resp.json()
            if not isinstance(data, dict) or data.get('status') is False:
                logger.error(f"AllHoldings API error: {data.get('message') if isinstance(data, dict) else 'Unknown'}")
                return {}
            payload = data.get('data', {}) or {}
            logger.info("Fetched all holdings summary")
            return payload
        except Exception as e:
            logger.exception(f"Error fetching all holdings: {e}")
            return {}

    def get_positions_book(self) -> List[Dict]:
        """
        Fetch positions (day/net) using SmartAPI order position endpoint.

        Returns:
            List of position dictionaries
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch positions book: No valid session")
                return []
            if not self.auth_token:
                logger.error("Auth token not available for positions API")
                return []
            import requests
            url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getPosition"
            headers = self._default_headers()
            resp = requests.post(url, json={}, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Positions API status {resp.status_code}: {resp.text[:200]}")
                return []
            ctype = resp.headers.get('content-type', '').lower()
            if 'application/json' not in ctype:
                logger.error(f"Positions API non-JSON response: {ctype}")
                return []
            data = resp.json()
            if not isinstance(data, dict) or data.get('status') is False:
                logger.error(f"Positions API error: {data.get('message') if isinstance(data, dict) else 'Unknown'}")
                return []
            positions = data.get('data', []) or []
            logger.info(f"Fetched {len(positions)} positions (book)")
            return positions
        except Exception as e:
            logger.exception(f"Error fetching positions book: {e}")
            return []

    def get_order_book(self) -> List[Dict]:
        """
        Fetch order book using SmartAPI endpoint.

        Returns:
            List of order dictionaries
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch order book: No valid session")
                return []
            if not self.auth_token:
                logger.error("Auth token not available for order book API")
                return []
            import requests
            url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getOrderBook"
            headers = self._default_headers()
            resp = requests.post(url, json={}, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.error(f"OrderBook API status {resp.status_code}: {resp.text[:200]}")
                return []
            ctype = resp.headers.get('content-type', '').lower()
            if 'application/json' not in ctype:
                logger.error(f"OrderBook API non-JSON response: {ctype}")
                return []
            data = resp.json()
            if not isinstance(data, dict) or data.get('status') is False:
                logger.error(f"OrderBook API error: {data.get('message') if isinstance(data, dict) else 'Unknown'}")
                return []
            orders = data.get('data', []) or []
            logger.info(f"Fetched {len(orders)} orders")
            return orders
        except Exception as e:
            logger.exception(f"Error fetching order book: {e}")
            return []

    def get_trade_book(self) -> List[Dict]:
        """
        Fetch trade book (day trades) using SmartAPI endpoint.

        Returns:
            List of trade dictionaries
        """
        try:
            if not self._ensure_session():
                logger.error("Cannot fetch trade book: No valid session")
                return []
            if not self.auth_token:
                logger.error("Auth token not available for trade book API")
                return []
            import requests
            url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getTradeBook"
            headers = self._default_headers()
            resp = requests.post(url, json={}, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.error(f"TradeBook API status {resp.status_code}: {resp.text[:200]}")
                return []
            ctype = resp.headers.get('content-type', '').lower()
            if 'application/json' not in ctype:
                logger.error(f"TradeBook API non-JSON response: {ctype}")
                return []
            data = resp.json()
            if not isinstance(data, dict) or data.get('status') is False:
                logger.error(f"TradeBook API error: {data.get('message') if isinstance(data, dict) else 'Unknown'}")
                return []
            trades = data.get('data', []) or []
            logger.info(f"Fetched {len(trades)} trades")
            return trades
        except Exception as e:
            logger.exception(f"Error fetching trade book: {e}")
            return []


class FyersBroker(BrokerInterface):
    """
    Fyers API broker implementation.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Fyers broker connection.
        
        Args:
            config: Configuration dictionary with broker credentials
        """
        self.api_key = config.get('api_key', '')
        self.access_token = config.get('access_token', '')
        self.client_id = config.get('client_id', '')
        self.api_secret = config.get('api_secret', '')
        # Note: Actual Fyers implementation would initialize session here
        # from fyers_apiv3 import fyersModel
        # self.fyers = fyersModel.FyersModel(client_id=self.client_id, ...)
    
    def place_order(
        self,
        symbol: str,
        strike: int,
        direction: str,
        quantity: int,
        order_type: str = "MARKET",
        price: Optional[float] = None
    ) -> Dict:
        """
        Place order via Fyers API.
        
        TODO: Implement actual Fyers API integration
        - Use fyers_apiv3.fyersModel
        - Authenticate and get access token
        - Place order using place_order method
        """
        # Placeholder implementation
        option_symbol = f"NSE:{symbol}{strike}{direction}"  # Format may vary
        
        order_data = {
            "symbol": option_symbol,
            "qty": quantity,
            "type": 2 if order_type == "MARKET" else 1,  # 1=LIMIT, 2=MARKET
            "side": 1,  # 1=BUY, -1=SELL
            "productType": "INTRADAY",
            "limitPrice": price if order_type == "LIMIT" else 0,
            "stopPrice": 0,
            "validity": "DAY",
            "disclosedQty": 0,
            "offlineOrder": "False"
        }
        
        # Placeholder return
        return {
            "status": True,
            "message": "Order placed successfully (placeholder)",
            "order_id": f"FYERS_{strike}_{direction}_{quantity}",
            "order_data": order_data
        }
    
    def get_positions(self) -> List[Dict]:
        """Get current positions from Fyers."""
        # Placeholder - would use fyers.positions()
        return []
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order via Fyers."""
        # Placeholder - would use fyers.cancel_order()
        return True
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get order status from Fyers."""
        # Placeholder
        return {"status": "PENDING", "order_id": order_id}
    
    def modify_order(
        self,
        order_id: str,
        price: Optional[float] = None,
        quantity: Optional[int] = None
    ) -> bool:
        """Modify order via Fyers."""
        # Placeholder
        return True


def create_broker_interface(config: Dict) -> BrokerInterface:
    """
    Factory function to create appropriate broker interface.
    
    Args:
        config: Configuration dictionary with broker type and credentials
    
    Returns:
        BrokerInterface instance
    """
    broker_type = config.get('broker', {}).get('type', 'angel').lower()
    
    broker_config = {
        'api_key': config.get('broker', {}).get('api_key', ''),
        'client_id': config.get('broker', {}).get('client_id', ''),
        'api_secret': config.get('broker', {}).get('api_secret', '')
    }
    
    if broker_type == 'angel':
        # Add SmartAPI-specific credentials
        broker_config['username'] = config.get('broker', {}).get('username', broker_config.get('client_id', ''))
        broker_config['pwd'] = config.get('broker', {}).get('pwd', '')
        broker_config['token'] = config.get('broker', {}).get('token', '')
        return AngelOneBroker(broker_config)
    elif broker_type == 'fyers':
        # Fyers still uses access_token (if available for backward compatibility)
        broker_config['access_token'] = config.get('broker', {}).get('access_token', '')
        return FyersBroker(broker_config)
    else:
        raise ValueError(f"Unsupported broker type: {broker_type}")

