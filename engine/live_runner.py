"""
Live Strategy Runner for real-time market monitoring and trade execution
"""

import threading
import time
from typing import Dict, Optional
from datetime import datetime
from logzero import logger

from engine.market_data import MarketDataProvider
from engine.signal_handler import SignalHandler
from engine.broker_connector import BrokerInterface
from engine.trade_logger import TradeLogger
from engine.position_monitor import PositionMonitor, PositionRules


class LiveStrategyRunner:
    """
    Manages live strategy execution with polling and trade execution.
    Runs in background thread to monitor market and execute trades.
    """
    
    def __init__(
        self,
        market_data_provider: MarketDataProvider,
        signal_handler: SignalHandler,
        broker: BrokerInterface,
        trade_logger: TradeLogger,
        config: Dict
    ):
        """
        Initialize LiveStrategyRunner.
        
        Args:
            market_data_provider: MarketDataProvider instance
            signal_handler: SignalHandler instance
            broker: BrokerInterface instance
            trade_logger: TradeLogger instance
            config: Configuration dictionary
        """
        self.market_data = market_data_provider
        self.signal_handler = signal_handler
        self.broker = broker
        self.trade_logger = trade_logger
        self.config = config
        
        # Running state
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        
        # Configuration from config file
        market_data_config = config.get('market_data', {})
        self.polling_interval = market_data_config.get('polling_interval_seconds', 900)  # 15 minutes default
        self.max_retries = market_data_config.get('max_retries', 3)
        self.retry_delay = market_data_config.get('retry_delay_seconds', 5)
        
        # Strategy config
        strategy_config = config.get('strategy', {})
        self.lot_size = config.get('lot_size', 75)
        # Use broker.default_qty if provided; fallback to 2 lots
        self.order_qty = config.get('broker', {}).get('default_qty', self.lot_size * 2)
        self.sl_points = strategy_config.get('sl', 30)
        self.rr_ratio = strategy_config.get('rr', 1.8)
        
        # Statistics
        self.last_fetch_time = None
        self.last_signal_time = None
        self.cycle_count = 0
        self.error_count = 0
        self.active_monitors = []
        
        logger.info(f"LiveStrategyRunner initialized (polling interval: {self.polling_interval}s)")
    
    def start(self) -> bool:
        """
        Start the live strategy monitoring loop.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            logger.warning("LiveStrategyRunner is already running")
            return False
        
        try:
            self._running = True
            self._stop_event.clear()
            
            # Create and start thread
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            
            logger.info("LiveStrategyRunner started")
            return True
            
        except Exception as e:
            logger.exception(f"Error starting LiveStrategyRunner: {e}")
            self._running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the live strategy monitoring loop.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self._running:
            logger.warning("LiveStrategyRunner is not running")
            return False
        
        try:
            self._running = False
            self._stop_event.set()
            
            # Wait for thread to finish (with timeout)
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5.0)
            
            logger.info("LiveStrategyRunner stopped")
            return True
            
        except Exception as e:
            logger.exception(f"Error stopping LiveStrategyRunner: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if runner is currently running."""
        return self._running
    
    def _run_loop(self):
        """
        Main polling loop (runs in background thread).
        """
        logger.info("Live strategy polling loop started")
        
        while self._running and not self._stop_event.is_set():
            try:
                # Run one cycle
                self._run_cycle()
                
                # Wait for next polling interval
                self._stop_event.wait(self.polling_interval)
                
            except Exception as e:
                logger.exception(f"Error in polling loop: {e}")
                self.error_count += 1
                
                # Wait a bit before retrying
                self._stop_event.wait(self.retry_delay)
        
        logger.info("Live strategy polling loop stopped")
    
    def _run_cycle(self):
        """
        Execute one cycle of market monitoring and strategy execution.
        """
        self.cycle_count += 1
        logger.info(f"Running strategy cycle #{self.cycle_count}")
        
        # Fetch latest market data
        try:
            self.market_data.refresh_data()
            self.last_fetch_time = datetime.now()
            
            # Get aggregated dataframes (prefer direct interval fetching with fallback to resampling)
            data_1h = self.market_data.get_1h_data(
                window_hours=self.config.get('market_data', {}).get('data_window_hours_1h', 48),
                use_direct_interval=True  # Try ONE_HOUR interval first
            )
            data_15m = self.market_data.get_15m_data(
                window_hours=self.config.get('market_data', {}).get('data_window_hours_15m', 12),
                use_direct_interval=True  # Try FIFTEEN_MINUTE interval first
            )
            
            # Check if we have sufficient data
            if data_1h.empty or data_15m.empty:
                logger.warning("Insufficient market data - empty dataframes. Skipping cycle. Check API connectivity or wait for market data.")
                return
            
            # Log candle counts for diagnostics
            logger.info(f"1H candles available: {len(data_1h)}, 15m candles available: {len(data_15m)}")
            
            if len(data_1h) < 20:  # Need at least 20 candles for Inside Bar detection
                logger.warning(f"Insufficient 1h data ({len(data_1h)} candles). Need at least 20. Skipping cycle. Data may be too recent or aggregation failed.")
                return
            
            if len(data_15m) < 5:  # Need at least 5 candles for breakout confirmation
                logger.warning(f"Insufficient 15m data ({len(data_15m)} candles). Need at least 5. Skipping cycle. Consider waiting 5-10 minutes for new candles.")
                if len(data_15m) == 0:
                    logger.warning("No valid 15-minute candles available. Strategy will skip this cycle. Waiting for next cycle may help.")
                return
            
            logger.info(f"Processing strategy with {len(data_1h)} 1h candles and {len(data_15m)} 15m candles")
            
            # Process signal
            signal = self.signal_handler.process_signal(data_1h, data_15m)
            
            if signal:
                self.last_signal_time = datetime.now()
                logger.info(f"Signal detected: {signal}")
                
                # Execute trade
                self._execute_trade(signal)
            else:
                logger.debug("No signal detected in this cycle")
                
        except Exception as e:
            logger.exception(f"Error in cycle execution: {e}")
            self.error_count += 1
    
    def _execute_trade(self, signal: Dict):
        """
        Execute trade based on signal.
        
        Args:
            signal: Signal dictionary from signal_handler
        """
        try:
            logger.info(f"Executing trade for signal: {signal}")
            
            # Extract signal parameters
            direction = signal.get('direction')
            strike = signal.get('strike')
            entry = signal.get('entry')
            
            if not all([direction, strike, entry]):
                logger.error(f"Invalid signal parameters: {signal}")
                return
            
            # Place order via broker
            order_result = self.broker.place_order(
                symbol="NIFTY",
                strike=strike,
                direction=direction,
                quantity=self.order_qty,
                order_type="MARKET"
            )
            
            if order_result.get('status'):
                order_id = order_result.get('order_id')
                logger.info(f"Order placed successfully: {order_id}")
                
                # Mark signal as executed
                self.signal_handler.mark_signal_executed(signal, order_id)
                
                # Log trade
                self.trade_logger.log_trade(
                    timestamp=datetime.now().isoformat(),
                    direction=direction,
                    strike=strike,
                    entry_price=entry,
                    quantity=self.order_qty,
                    order_id=order_id,
                    status="OPEN",
                    reason=signal.get('reason', 'Inside Bar breakout')
                )
                
                logger.info(f"Trade logged: Order {order_id}, {direction} {strike} @ {entry}")

                # Start PositionMonitor for this position
                try:
                    symboltoken = order_result.get('symboltoken')
                    exchange = order_result.get('exchange', 'NFO')
                    pm_cfg = self.config.get('position_management', {})
                    rules = PositionRules(
                        sl_points=int(pm_cfg.get('sl_points', 30)),
                        trail_points=int(pm_cfg.get('trail_points', 10)),
                        book1_points=int(pm_cfg.get('book1_points', 40)),
                        book2_points=int(pm_cfg.get('book2_points', 54)),
                        book1_ratio=float(pm_cfg.get('book1_ratio', 0.5)),
                    )
                    monitor = PositionMonitor(
                        broker=self.broker,
                        symbol_token=symboltoken,
                        exchange=exchange,
                        entry_price=entry,
                        total_qty=self.order_qty,
                        rules=rules,
                        order_id=order_id,
                    )
                    if monitor.start():
                        self.active_monitors.append(monitor)
                        logger.info("Position monitor started for order {order_id}")
                except Exception as e:
                    logger.exception(f"Failed to start PositionMonitor: {e}")
                
            else:
                error_msg = order_result.get('message', 'Unknown error')
                logger.error(f"Order placement failed: {error_msg}")
                
                # Log failed trade attempt
                self.trade_logger.log_trade(
                    timestamp=datetime.now().isoformat(),
                    direction=direction,
                    strike=strike,
                    entry_price=entry,
                    quantity=self.order_qty,
                    order_id=None,
                    status="FAILED",
                    reason=f"Order failed: {error_msg}"
                )
                
        except Exception as e:
            logger.exception(f"Error executing trade: {e}")
    
    def get_status(self) -> Dict:
        """
        Get current status of the live runner.
        
        Returns:
            Dictionary with status information
        """
        return {
            'running': self._running,
            'cycle_count': self.cycle_count,
            'error_count': self.error_count,
            'last_fetch_time': self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
            'polling_interval': self.polling_interval
        }

