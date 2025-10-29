"""
Signal Handler for processing and validating trading signals
"""

import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime
from engine.strategy_engine import check_for_signal


class SignalHandler:
    """
    Handles signal processing, validation, and trade signal generation.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize SignalHandler with configuration.
        
        Args:
            config: Configuration dictionary with strategy parameters
        """
        self.config = config
        self.active_signals = []
        self.signal_history = []
    
    def validate_signal(self, signal: Dict) -> bool:
        """
        Validate generated signal against filters and rules.
        
        Args:
            signal: Signal dictionary from strategy_engine
        
        Returns:
            True if signal is valid, False otherwise
        """
        if signal is None:
            return False
        
        filters = self.config.get('strategy', {}).get('filters', {})
        
        # Check volume spike filter
        if filters.get('volume_spike', False):
            # Volume validation should be done in strategy_engine
            # Additional validation can be added here
            pass
        
        # Check open range avoidance filter
        if filters.get('avoid_open_range', False):
            current_hour = datetime.now().hour
            current_minute = datetime.now().minute
            # Avoid trading in first 30 minutes (9:00-9:30 IST)
            if current_hour == 9 and current_minute < 30:
                return False
        
        # Validate signal structure
        required_fields = ['direction', 'strike', 'entry', 'sl', 'tp']
        for field in required_fields:
            if field not in signal:
                return False
        
        # Validate direction
        if signal['direction'] not in ['CE', 'PE']:
            return False
        
        # Validate price levels
        if signal['sl'] >= signal['entry'] or signal['tp'] <= signal['entry']:
            return False
        
        return True
    
    def process_signal(
        self,
        data_1h: pd.DataFrame,
        data_15m: pd.DataFrame
    ) -> Optional[Dict]:
        """
        Process market data and generate validated signal.
        
        Args:
            data_1h: 1-hour OHLC data
            data_15m: 15-minute OHLCV data
        
        Returns:
            Validated signal dictionary or None
        """
        # Get strategy configuration
        strategy_config = {
            'sl': self.config.get('strategy', {}).get('sl', 30),
            'rr': self.config.get('strategy', {}).get('rr', 1.8)
        }
        
        # Generate signal
        signal = check_for_signal(data_1h, data_15m, strategy_config)
        
        # Validate signal
        if not self.validate_signal(signal):
            return None
        
        # Add timestamp
        signal['timestamp'] = datetime.now().isoformat()
        signal['status'] = 'pending'
        
        # Store in history
        self.signal_history.append(signal)
        
        return signal
    
    def get_active_signals(self) -> List[Dict]:
        """
        Get list of active trading signals.
        
        Returns:
            List of active signal dictionaries
        """
        return [s for s in self.active_signals if s.get('status') == 'active']
    
    def mark_signal_executed(self, signal: Dict, order_id: str):
        """
        Mark signal as executed with order ID.
        
        Args:
            signal: Signal dictionary
            order_id: Broker order ID
        """
        signal['status'] = 'executed'
        signal['order_id'] = order_id
        signal['executed_at'] = datetime.now().isoformat()
        
        if signal not in self.active_signals:
            self.active_signals.append(signal)
    
    def mark_signal_closed(self, signal: Dict, exit_price: float, pnl: float):
        """
        Mark signal as closed with exit details.
        
        Args:
            signal: Signal dictionary
            exit_price: Exit price
            pnl: Profit/Loss amount
        """
        signal['status'] = 'closed'
        signal['exit_price'] = exit_price
        signal['pnl'] = pnl
        signal['closed_at'] = datetime.now().isoformat()
        
        # Remove from active signals
        if signal in self.active_signals:
            self.active_signals.remove(signal)

