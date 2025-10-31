"""
Strategy Engine for NIFTY Options Trading System
Implements Inside Bar detection and 15-minute breakout confirmation
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Tuple
from logzero import logger


def detect_inside_bar(data_1h: pd.DataFrame) -> List[int]:
    """
    Detect Inside Bar patterns in 1-hour timeframe data.
    
    An Inside Bar is when a candle is completely contained within 
    the previous candle's high and low range.
    
    Args:
        data_1h: DataFrame with OHLC data for 1-hour timeframe
                 Must have columns: ['High', 'Low', 'Open', 'Close', 'Date']
    
    Returns:
        List of indices where Inside Bar patterns are detected
    """
    inside_bars = []
    
    if len(data_1h) < 2:
        logger.debug("Insufficient data for Inside Bar detection (need at least 2 candles)")
        return inside_bars
    
    logger.info(f"🔍 Starting Inside Bar detection scan on {len(data_1h)} 1-hour candles")
    
    for i in range(2, len(data_1h)):
        # Check if current candle is inside the previous candle (i-1)
        current_high = data_1h['High'].iloc[i]
        current_low = data_1h['Low'].iloc[i]
        prev_high = data_1h['High'].iloc[i-1]
        prev_low = data_1h['Low'].iloc[i-1]
        
        # Get timestamps for logging
        current_time = data_1h['Date'].iloc[i] if 'Date' in data_1h.columns else f"Candle_{i}"
        prev_time = data_1h['Date'].iloc[i-1] if 'Date' in data_1h.columns else f"Candle_{i-1}"
        
        # Log reference candle (previous candle)
        if i == 2:
            logger.info(f"📊 Reference candle: {prev_time} => High: {prev_high:.2f}, Low: {prev_low:.2f}")
        
        # Inside bar condition: 
        # The CURRENT candle (i) must be COMPLETELY inside the PREVIOUS candle (i-1)
        # This means:
        # - Current high MUST BE LESS than previous high (strictly <, not <=)
        # - Current low MUST BE GREATER than previous low (strictly >, not >=)
        # Both conditions must be true simultaneously
        
        high_check = current_high < prev_high  # Strictly less
        low_check = current_low > prev_low     # Strictly greater
        is_inside = high_check and low_check
        
        logger.debug(
            f"Candle at {current_time} => "
            f"High: {current_high:.2f} {'< ' if high_check else '>= '} {prev_high:.2f} (ref) | "
            f"Low: {current_low:.2f} {'> ' if low_check else '<= '} {prev_low:.2f} (ref)"
        )
        
        if is_inside:
            logger.info(
                f"✅ Inside Bar detected at {current_time} | "
                f"High: {current_high:.2f} < {prev_high:.2f}, Low: {current_low:.2f} > {prev_low:.2f} | "
                f"Within range: {prev_low:.2f} - {prev_high:.2f}"
            )
            inside_bars.append(i)
        else:
            # Log detailed reason if not inside
            if not high_check and not low_check:
                reason = f"High {current_high:.2f} >= Ref {prev_high:.2f} AND Low {current_low:.2f} <= Ref {prev_low:.2f} (outside range)"
            elif not high_check:
                reason = f"High {current_high:.2f} >= Ref {prev_high:.2f} (must be < {prev_high:.2f})"
            elif not low_check:
                reason = f"Low {current_low:.2f} <= Ref {prev_low:.2f} (must be > {prev_low:.2f})"
            else:
                reason = "Unknown"
            logger.debug(f"❌ Not an Inside Bar at {current_time}: {reason}")
    
    if inside_bars:
        logger.info(f"🎯 Total Inside Bars detected: {len(inside_bars)} at indices: {inside_bars}")
    else:
        logger.debug(f"🔍 No Inside Bar patterns found in {len(data_1h)} candles")
    
    return inside_bars


def confirm_breakout(
    data_15m: pd.DataFrame,
    range_high: float,
    range_low: float,
    volume_threshold_multiplier: float = 1.0
) -> Optional[str]:
    """
    Confirm breakout on 15-minute timeframe with volume validation.
    Checks up to the last 5 candles for breakout confirmation.
    
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
    
    # Get last 5 candles for confirmation check
    recent = data_15m.tail(5)
    
    # Calculate average volume over last 5 candles
    avg_volume = recent['Volume'].mean()
    volume_threshold = avg_volume * volume_threshold_multiplier
    
    logger.debug(
        f"🔍 Checking breakout on {len(recent)} recent 15m candles | "
        f"Range: {range_low:.2f} - {range_high:.2f} | "
        f"Volume threshold: {volume_threshold:.0f} (avg: {avg_volume:.0f} × {volume_threshold_multiplier})"
    )
    
    # Check each of the last 5 candles for breakout
    # Start from oldest to newest (first valid breakout wins)
    for i in range(len(recent)):
        close = recent['Close'].iloc[i]
        high = recent['High'].iloc[i]
        low = recent['Low'].iloc[i]
        vol = recent['Volume'].iloc[i]
        
        # Get timestamp for logging
        candle_time = recent['Date'].iloc[i] if 'Date' in recent.columns else f"Candle_{i}"
        
        # Bullish breakout (Call option) - close above range high with volume confirmation
        if close > range_high and vol > volume_threshold:
            logger.info(
                f"✅ Bullish breakout (CE) confirmed at {candle_time} | "
                f"Close: {close:.2f} > Range High: {range_high:.2f} | "
                f"Volume: {vol:.0f} > Threshold: {volume_threshold:.0f}"
            )
            return "CE"
        
        # Bearish breakout (Put option) - close below range low with volume confirmation
        elif close < range_low and vol > volume_threshold:
            logger.info(
                f"✅ Bearish breakout (PE) confirmed at {candle_time} | "
                f"Close: {close:.2f} < Range Low: {range_low:.2f} | "
                f"Volume: {vol:.0f} > Threshold: {volume_threshold:.0f}"
            )
            return "PE"
        
        # Log why this candle didn't trigger breakout
        logger.debug(
            f"Candle at {candle_time} | "
            f"Close: {close:.2f}, Volume: {vol:.0f} | "
            f"Range check: {range_low:.2f} <= Close <= {range_high:.2f}, "
            f"Volume check: {vol:.0f} <= {volume_threshold:.0f}"
        )
    
    logger.debug("❌ No breakout confirmed in last 5 15m candles")
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
    # Validate data sufficiency
    if data_1h.empty or data_15m.empty:
        logger.warning("Empty dataframes provided to check_for_signal")
        return None
    
    # Ensure we have enough 1H data for Inside Bar detection
    # Need at least 20 candles for reliable pattern detection
    if len(data_1h) < 20:
        logger.warning(f"Insufficient 1H data ({len(data_1h)} candles). Need at least 20 candles. Skipping signal check.")
        return None
    
    # Ensure we have enough 15m data for breakout confirmation
    # Need at least 5 candles for volume confirmation
    if len(data_15m) < 5:
        logger.warning(f"Insufficient 15m data ({len(data_15m)} candles). Need at least 5 candles. Skipping signal check.")
        return None
    
    # Detect Inside Bar patterns
    inside_bars = detect_inside_bar(data_1h)
    
    if not inside_bars:
        logger.debug(f"No Inside Bar patterns detected in {len(data_1h)} 1H candles")
        return None
    
    logger.debug(f"Found {len(inside_bars)} Inside Bar pattern(s)")
    
    # Get the most recent Inside Bar
    latest_inside_bar_idx = inside_bars[-1]
    
    # IMPORTANT: Inside Bar is at index 'latest_inside_bar_idx'
    # The reference candle (parent) is at 'latest_inside_bar_idx - 1'
    # The range comes from the reference candle (the one that contains the inside bar)
    inside_bar_candle = data_1h.iloc[latest_inside_bar_idx]
    reference_candle = data_1h.iloc[latest_inside_bar_idx - 1]
    
    # Extract values
    inside_bar_high = inside_bar_candle['High']
    inside_bar_low = inside_bar_candle['Low']
    range_high = reference_candle['High']  # Parent candle's high
    range_low = reference_candle['Low']    # Parent candle's low
    
    # Get timestamps for logging
    inside_bar_time = inside_bar_candle['Date'] if 'Date' in inside_bar_candle.index else f"Index_{latest_inside_bar_idx}"
    ref_time = reference_candle['Date'] if 'Date' in reference_candle.index else f"Index_{latest_inside_bar_idx - 1}"
    
    # Format timestamps for display
    if hasattr(inside_bar_time, 'strftime'):
        inside_bar_time_str = inside_bar_time.strftime("%Y-%m-%d %H:%M:%S IST")
    else:
        inside_bar_time_str = str(inside_bar_time)
    if hasattr(ref_time, 'strftime'):
        ref_time_str = ref_time.strftime("%Y-%m-%d %H:%M:%S IST")
    else:
        ref_time_str = str(ref_time)
    
    logger.info(
        f"📊 Using most recent Inside Bar at {inside_bar_time_str} | "
        f"Reference candle: {ref_time_str} | "
        f"Inside Bar Range: {inside_bar_low:.2f} - {inside_bar_high:.2f} | "
        f"Breakout range (from reference): {range_low:.2f} - {range_high:.2f}"
    )
    
    # Verify the inside bar logic is correct
    if not (inside_bar_high < range_high and inside_bar_low > range_low):
        logger.error(
            f"⚠️ WARNING: Inside Bar validation failed! "
            f"Inside Bar High ({inside_bar_high:.2f}) should be < Ref High ({range_high:.2f}) AND "
            f"Inside Bar Low ({inside_bar_low:.2f}) should be > Ref Low ({range_low:.2f})"
        )
    
    # Check for breakout confirmation
    direction = confirm_breakout(
        data_15m,
        range_high,
        range_low,
        volume_threshold_multiplier=1.0
    )
    
    if direction is None:
        logger.debug(
            f"🔍 No breakout confirmed in {len(data_15m)} 15m candles | "
            f"Range: {range_low:.2f} - {range_high:.2f}"
        )
        return None
    
    logger.info(
        f"✅ Breakout confirmed: {direction} | "
        f"Range: {range_low:.2f} - {range_high:.2f}"
    )
    
    # Get current price for strike calculation
    current_nifty_price = data_15m['Close'].iloc[-1]
    
    # Calculate strike with ATM offset from config
    atm_offset = config.get('atm_offset', 0)
    strike = calculate_strike_price(current_nifty_price, direction, atm_offset=atm_offset)
    
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

