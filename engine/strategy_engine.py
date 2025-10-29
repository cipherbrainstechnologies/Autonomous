"""
Strategy Engine for NIFTY Options Trading System
Implements Inside Bar detection and 15-minute breakout confirmation
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Tuple


def detect_inside_bar(data_1h: pd.DataFrame) -> List[int]:
    """
    Detect Inside Bar patterns in 1-hour timeframe data.
    
    An Inside Bar is when a candle is completely contained within 
    the previous candle's high and low range.
    
    Args:
        data_1h: DataFrame with OHLC data for 1-hour timeframe
                 Must have columns: ['High', 'Low', 'Open', 'Close']
    
    Returns:
        List of indices where Inside Bar patterns are detected
    """
    inside_bars = []
    
    if len(data_1h) < 2:
        return inside_bars
    
    for i in range(2, len(data_1h)):
        # Check if current candle is inside the previous candle (i-1)
        current_high = data_1h['High'].iloc[i]
        current_low = data_1h['Low'].iloc[i]
        prev_high = data_1h['High'].iloc[i-1]
        prev_low = data_1h['Low'].iloc[i-1]
        
        # Inside bar condition: current high < prev high AND current low > prev low
        if current_high < prev_high and current_low > prev_low:
            inside_bars.append(i)
    
    return inside_bars


def confirm_breakout(
    data_15m: pd.DataFrame,
    range_high: float,
    range_low: float,
    volume_threshold_multiplier: float = 1.0
) -> Optional[str]:
    """
    Confirm breakout on 15-minute timeframe with volume validation.
    
    Args:
        data_15m: DataFrame with OHLCV data for 15-minute timeframe
                  Must have columns: ['Close', 'Volume', 'High', 'Low']
        range_high: Upper bound of the Inside Bar range
        range_low: Lower bound of the Inside Bar range
        volume_threshold_multiplier: Multiplier for volume average (default: 1.0)
    
    Returns:
        "CE" for Call option (bullish breakout)
        "PE" for Put option (bearish breakout)
        None if no breakout confirmed
    """
    if len(data_15m) < 5:
        return None
    
    # Calculate average volume over last 5 candles
    avg_volume = data_15m['Volume'].tail(5).mean()
    volume_threshold = avg_volume * volume_threshold_multiplier
    
    # Check for breakout from most recent candle
    latest_close = data_15m['Close'].iloc[-1]
    latest_high = data_15m['High'].iloc[-1]
    latest_low = data_15m['Low'].iloc[-1]
    latest_volume = data_15m['Volume'].iloc[-1]
    
    # Bullish breakout (Call option)
    if latest_close > range_high and latest_volume > volume_threshold:
        return "CE"
    
    # Bearish breakout (Put option)
    elif latest_close < range_low and latest_volume > volume_threshold:
        return "PE"
    
    return None


def calculate_strike_price(
    current_price: float,
    direction: str,
    atm_offset: int = 0
) -> int:
    """
    Calculate option strike price based on current price and direction.
    
    Args:
        current_price: Current NIFTY index price
        direction: "CE" for Call, "PE" for Put
        atm_offset: Offset from ATM (0 = ATM, positive = OTM for calls)
    
    Returns:
        Strike price rounded to nearest 50
    """
    # NIFTY strikes are in multiples of 50
    base_strike = round(current_price / 50) * 50
    
    if direction == "CE":
        return base_strike + atm_offset
    elif direction == "PE":
        return base_strike - atm_offset
    else:
        return int(base_strike)


def calculate_sl_tp_levels(
    entry_price: float,
    stop_loss_points: int,
    risk_reward_ratio: float
) -> Tuple[float, float]:
    """
    Calculate Stop Loss and Take Profit levels based on entry and risk parameters.
    
    Args:
        entry_price: Entry price of the option
        stop_loss_points: Stop loss in points
        risk_reward_ratio: Risk-Reward ratio (e.g., 1.8 = 1.8x risk)
    
    Returns:
        Tuple of (stop_loss_price, take_profit_price)
    """
    stop_loss = entry_price - stop_loss_points
    take_profit = entry_price + (stop_loss_points * risk_reward_ratio)
    
    return (stop_loss, take_profit)


def check_for_signal(
    data_1h: pd.DataFrame,
    data_15m: pd.DataFrame,
    config: Dict
) -> Optional[Dict]:
    """
    Main signal detection function that combines Inside Bar detection
    and breakout confirmation.
    
    Args:
        data_1h: 1-hour OHLC data
        data_15m: 15-minute OHLCV data
        config: Configuration dictionary with strategy parameters
    
    Returns:
        Signal dictionary with trade details if signal detected, None otherwise
        {
            'direction': 'CE' or 'PE',
            'strike': strike price,
            'entry': entry price,
            'sl': stop loss price,
            'tp': take profit price,
            'range_high': Inside Bar high,
            'range_low': Inside Bar low,
            'reason': signal generation reason
        }
    """
    # Detect Inside Bar patterns
    inside_bars = detect_inside_bar(data_1h)
    
    if not inside_bars:
        return None
    
    # Get the most recent Inside Bar
    latest_inside_bar_idx = inside_bars[-1]
    range_high = data_1h['High'].iloc[latest_inside_bar_idx - 1]
    range_low = data_1h['Low'].iloc[latest_inside_bar_idx - 1]
    
    # Check for breakout confirmation
    direction = confirm_breakout(
        data_15m,
        range_high,
        range_low,
        volume_threshold_multiplier=1.0
    )
    
    if direction is None:
        return None
    
    # Get current price for strike calculation
    current_nifty_price = data_15m['Close'].iloc[-1]
    
    # Calculate strike (using ATM for now)
    strike = calculate_strike_price(current_nifty_price, direction, atm_offset=0)
    
    # For this system, entry price would be fetched from broker
    # Placeholder: use a reasonable estimate
    entry_price = current_nifty_price  # This should be actual option price
    
    # Calculate SL and TP
    sl_points = config.get('sl', 30)
    rr_ratio = config.get('rr', 1.8)
    stop_loss, take_profit = calculate_sl_tp_levels(
        entry_price,
        sl_points,
        rr_ratio
    )
    
    signal = {
        'direction': direction,
        'strike': strike,
        'entry': entry_price,
        'sl': stop_loss,
        'tp': take_profit,
        'range_high': range_high,
        'range_low': range_low,
        'reason': f"Inside Bar breakout on {direction} side with volume confirmation"
    }
    
    return signal

