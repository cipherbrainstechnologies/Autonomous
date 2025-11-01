"""
Trade Management Functions for NIFTY Options Trading
Modular functions for signal detection, trade eligibility, position management, and exits
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, Any
from datetime import datetime, timedelta
from logzero import logger


@dataclass
class Signal:
    """Signal candle with breakout range"""
    range_high: float
    range_low: float
    ts: datetime


@dataclass
class Option:
    """Option contract details"""
    symbol: str
    strike: int
    expiry: str
    lot: int = 75


@dataclass
class Exit:
    """Exit signal for position"""
    reason: str
    exit_price: float
    qty: int
    timestamp: datetime


@dataclass
class TradingContext:
    """Context for trading decisions"""
    spot: float
    iv: float  # Implied Volatility
    atr: float  # Average True Range
    spread: float  # Bid-Ask spread
    gap_pct: float  # Gap percentage from previous close
    swings: list  # Recent swing highs/lows
    is_expiry_day: bool
    account_risk: float  # Risk amount in rupees
    config: Dict[str, Any]


def detect_signal_candle(h1: pd.DataFrame) -> Optional[Signal]:
    """
    Detect Inside Bar pattern in 1-hour timeframe and return signal with breakout range.
    
    Args:
        h1: DataFrame with 1-hour OHLC data (columns: Date, Open, High, Low, Close, Volume)
    
    Returns:
        Signal object with range_high, range_low, and timestamp, or None if no pattern
    """
    if h1.empty or len(h1) < 2:
        logger.debug("Insufficient data for signal detection (need at least 2 candles)")
        return None
    
    # Detect Inside Bar patterns
    inside_bars = []
    for i in range(1, len(h1)):
        current_high = h1['High'].iloc[i]
        current_low = h1['Low'].iloc[i]
        prev_high = h1['High'].iloc[i-1]
        prev_low = h1['Low'].iloc[i-1]
        
        # Inside bar condition: current candle completely inside previous candle
        if current_high < prev_high and current_low > prev_low:
            inside_bars.append(i)
    
    if not inside_bars:
        logger.debug("No Inside Bar pattern detected")
        return None
    
    # Use the most recent Inside Bar
    latest_idx = inside_bars[-1]
    reference_idx = latest_idx - 1
    
    # Range comes from the reference candle (parent candle)
    range_high = h1['High'].iloc[reference_idx]
    range_low = h1['Low'].iloc[reference_idx]
    
    # Get timestamp from the inside bar candle
    if 'Date' in h1.columns:
        ts = h1['Date'].iloc[latest_idx]
        if isinstance(ts, pd.Timestamp):
            ts = ts.to_pydatetime()
    else:
        ts = datetime.now()
    
    logger.info(
        f"Signal candle detected: range [{range_low:.2f}, {range_high:.2f}] "
        f"at {ts}"
    )
    
    return Signal(range_high=range_high, range_low=range_low, ts=ts)


def breakout_side(h1_close: float, signal: Signal) -> Optional[str]:
    """
    Determine breakout side based on close price relative to signal range.
    
    Args:
        h1_close: Current 1-hour close price
        signal: Signal object with range_high and range_low
    
    Returns:
        "CE" for Call option (bullish breakout above range_high)
        "PE" for Put option (bearish breakout below range_low)
        None if no breakout
    """
    if signal is None:
        return None
    
    if h1_close > signal.range_high:
        logger.debug(f"Bullish breakout: {h1_close:.2f} > {signal.range_high:.2f} (CE)")
        return "CE"
    elif h1_close < signal.range_low:
        logger.debug(f"Bearish breakout: {h1_close:.2f} < {signal.range_low:.2f} (PE)")
        return "PE"
    else:
        logger.debug(
            f"No breakout: {signal.range_low:.2f} <= {h1_close:.2f} <= {signal.range_high:.2f}"
        )
        return None


def eligible_to_trade(context: TradingContext) -> bool:
    """
    Check if conditions are eligible for trading based on filters.
    
    Filters:
    - Gap filter: Avoid trading on large gaps
    - IV filter: Check implied volatility levels
    - Spread filter: Check bid-ask spread
    - ATR filter: Check volatility conditions
    
    Args:
        context: TradingContext with market conditions
    
    Returns:
        True if eligible to trade, False otherwise
    """
    if context is None:
        return False
    
    config = context.config.get('filters', {})
    
    # Gap filter: Avoid trading on large gaps (>2%)
    max_gap_pct = config.get('max_gap_pct', 2.0)
    if abs(context.gap_pct) > max_gap_pct:
        logger.debug(f"Gap filter: gap {context.gap_pct:.2f}% exceeds {max_gap_pct}%")
        return False
    
    # IV filter: Check if IV is within acceptable range
    min_iv = config.get('min_iv', 10.0)
    max_iv = config.get('max_iv', 50.0)
    if context.iv < min_iv or context.iv > max_iv:
        logger.debug(f"IV filter: IV {context.iv:.2f} outside range [{min_iv}, {max_iv}]")
        return False
    
    # Spread filter: Check bid-ask spread (as percentage of spot)
    max_spread_pct = config.get('max_spread_pct', 0.5)
    spread_pct = (context.spread / context.spot) * 100 if context.spot > 0 else 0
    if spread_pct > max_spread_pct:
        logger.debug(f"Spread filter: spread {spread_pct:.2f}% exceeds {max_spread_pct}%")
        return False
    
    # ATR filter: Check if ATR indicates acceptable volatility
    min_atr_pct = config.get('min_atr_pct', 0.5)
    max_atr_pct = config.get('max_atr_pct', 3.0)
    atr_pct = (context.atr / context.spot) * 100 if context.spot > 0 else 0
    if atr_pct < min_atr_pct or atr_pct > max_atr_pct:
        logger.debug(f"ATR filter: ATR {atr_pct:.2f}% outside range [{min_atr_pct}, {max_atr_pct}]")
        return False
    
    logger.debug("All filters passed - eligible to trade")
    return True


def pick_option(symbol: str, spot: float, side: str) -> Option:
    """
    Select option contract based on symbol, spot price, and side.
    
    Args:
        symbol: Base symbol (e.g., "NIFTY")
        spot: Current spot price
        side: "CE" for Call, "PE" for Put
    
    Returns:
        Option object with symbol, strike, expiry, and lot size
    """
    if side not in ["CE", "PE"]:
        raise ValueError(f"Invalid side: {side}. Must be 'CE' or 'PE'")
    
    # Calculate ATM strike (rounded to nearest 50 for NIFTY)
    base_strike = round(spot / 50) * 50
    
    # For now, use ATM strike (can be extended with offset from config)
    strike = int(base_strike)
    
    # Calculate nearest expiry (Thursday for NIFTY weekly options)
    # For simplicity, use next Thursday or current week's Thursday
    today = datetime.now()
    days_until_thursday = (3 - today.weekday()) % 7
    if days_until_thursday == 0 and today.hour >= 15:  # If Thursday and after market close
        days_until_thursday = 7
    
    expiry_date = today + timedelta(days=days_until_thursday)
    expiry = expiry_date.strftime("%Y-%m-%d")
    
    # Default lot size for NIFTY options
    lot = 75
    
    logger.info(
        f"Selected option: {symbol} {strike} {side} exp {expiry} (lot={lot})"
    )
    
    return Option(symbol=symbol, strike=strike, expiry=expiry, lot=lot)


def compute_lots(acct_risk: float, entry_premium: float) -> int:
    """
    Calculate number of lots based on account risk and entry premium.
    
    Args:
        acct_risk: Risk amount in rupees (max loss per trade)
        entry_premium: Entry premium per lot
    
    Returns:
        Number of lots (minimum 1)
    """
    if entry_premium <= 0:
        logger.warning(f"Invalid entry premium: {entry_premium}")
        return 1
    
    # Risk per lot = entry premium (assuming 100% loss as worst case)
    # Alternatively, could use initial_sl to calculate risk per lot
    risk_per_lot = entry_premium
    
    # Calculate lots based on account risk
    lots = int(acct_risk / risk_per_lot) if risk_per_lot > 0 else 1
    
    # Ensure minimum 1 lot
    lots = max(1, lots)
    
    logger.debug(
        f"Computed lots: {lots} (risk={acct_risk}, premium={entry_premium:.2f}, "
        f"risk_per_lot={risk_per_lot:.2f})"
    )
    
    return lots


def initial_sl(entry_premium: float) -> float:
    """
    Calculate initial stop loss as 0.65 * entry premium.
    
    Args:
        entry_premium: Entry premium price
    
    Returns:
        Stop loss price (0.65 * entry_premium)
    """
    sl = 0.65 * entry_premium
    logger.debug(f"Initial SL: {sl:.2f} (65% of entry {entry_premium:.2f})")
    return sl


def update_trailing(
    context: TradingContext,
    entry_premium: float,
    cur_premium: float,
    atr: float,
    swings: list,
    iv: float
) -> float:
    """
    Update trailing stop loss based on context, current premium, ATR, swings, and IV.
    
    Args:
        context: TradingContext with market conditions
        entry_premium: Original entry premium
        cur_premium: Current premium price
        atr: Average True Range
        swings: List of recent swing highs/lows
        iv: Current implied volatility
    
    Returns:
        Updated trailing stop loss price
    """
    # Base trailing: use ATR multiplier
    atr_multiplier = context.config.get('trailing', {}).get('atr_multiplier', 1.5)
    base_trail = cur_premium - (atr * atr_multiplier)
    
    # Adjust based on IV: higher IV = wider trailing
    iv_adjustment = context.config.get('trailing', {}).get('iv_adjustment', 0.1)
    iv_factor = 1.0 + (iv / 100.0) * iv_adjustment
    adjusted_trail = base_trail * iv_factor
    
    # Use swing-based trailing if swings available
    if swings and len(swings) > 0:
        # Use recent swing low as trailing reference
        recent_swing = min(swings[-3:]) if len(swings) >= 3 else min(swings)
        swing_trail = recent_swing - (atr * 0.5)  # Half ATR below swing
        
        # Use the more conservative (higher) trailing stop
        adjusted_trail = max(adjusted_trail, swing_trail)
    
    # Ensure trailing SL never goes below initial SL
    initial_sl_price = initial_sl(entry_premium)
    final_trail = max(adjusted_trail, initial_sl_price)
    
    # Ensure trailing SL never goes above entry (for long positions)
    final_trail = min(final_trail, entry_premium)
    
    logger.debug(
        f"Trailing SL updated: {final_trail:.2f} (entry={entry_premium:.2f}, "
        f"current={cur_premium:.2f}, ATR={atr:.2f}, IV={iv:.2f})"
    )
    
    return final_trail


def time_expiry_exit(
    now: datetime,
    is_expiry_day: bool,
    premium: float,
    position: Dict
) -> Optional[Exit]:
    """
    Check if position should be exited due to expiry day timing.
    
    Args:
        now: Current datetime
        is_expiry_day: Whether today is expiry day
        premium: Current premium price
        position: Position dictionary with quantity and other details
    
    Returns:
        Exit object if exit needed, None otherwise
    """
    if not is_expiry_day:
        return None
    
    # Exit logic for expiry day
    config = position.get('config', {})
    exit_time = config.get('expiry_exit_time', '15:00')  # Default: 3 PM IST
    
    try:
        exit_hour, exit_minute = map(int, exit_time.split(':'))
        exit_datetime = now.replace(hour=exit_hour, minute=exit_minute, second=0, microsecond=0)
    except:
        # Default to 3 PM if parsing fails
        exit_datetime = now.replace(hour=15, minute=0, second=0, microsecond=0)
    
    # Exit if current time is at or after exit time
    if now >= exit_datetime:
        qty = position.get('quantity', 0)
        if qty > 0:
            logger.info(
                f"Expiry day exit triggered at {now} (exit_time={exit_time})"
            )
            return Exit(
                reason="Expiry day exit",
                exit_price=premium,
                qty=qty,
                timestamp=now
            )
    
    return None


def manage_trade_tick(
    position: Dict,
    current_premium: float,
    context: TradingContext,
    current_sl: float
) -> Optional[Tuple[str, Optional[Dict]]]:
    """
    Manage trade on each tick - check for exits or modifications.
    
    Args:
        position: Position dictionary with entry details
        current_premium: Current premium price
        context: TradingContext with market conditions
        current_sl: Current stop loss level
    
    Returns:
        Tuple of (action, params) where:
        - action: "exit", "modify_sl", or None
        - params: Dictionary with exit/modify details, or None
        None if no action needed
    """
    entry_premium = position.get('entry_premium', 0)
    quantity = position.get('quantity', 0)
    
    if quantity <= 0:
        return None
    
    # Check stop loss
    if current_premium <= current_sl:
        logger.info(f"Stop loss hit: {current_premium:.2f} <= {current_sl:.2f}")
        return ("exit", {
            "reason": "Stop loss",
            "exit_price": current_premium,
            "qty": quantity
        })
    
    # Check take profit (if configured)
    tp_config = context.config.get('take_profit', {})
    if tp_config:
        tp_points = tp_config.get('points', 54)  # Default from config
        tp_price = entry_premium + tp_points
        
        if current_premium >= tp_price:
            logger.info(f"Take profit hit: {current_premium:.2f} >= {tp_price:.2f}")
            return ("exit", {
                "reason": "Take profit",
                "exit_price": current_premium,
                "qty": quantity
            })
    
    # Check trailing stop update
    if 'trailing' in context.config:
        # Calculate new trailing SL
        swings = context.swings if context.swings else []
        new_trail_sl = update_trailing(
            context=context,
            entry_premium=entry_premium,
            cur_premium=current_premium,
            atr=context.atr,
            swings=swings,
            iv=context.iv
        )
        
        # If new trailing SL is higher than current, update it
        if new_trail_sl > current_sl:
            logger.info(f"Trailing SL update: {current_sl:.2f} -> {new_trail_sl:.2f}")
            return ("modify_sl", {
                "new_sl": new_trail_sl,
                "reason": "Trailing stop update"
            })
    
    # Check expiry day exit
    if context.is_expiry_day:
        exit_signal = time_expiry_exit(
            now=datetime.now(),
            is_expiry_day=True,
            premium=current_premium,
            position=position
        )
        if exit_signal:
            return ("exit", {
                "reason": exit_signal.reason,
                "exit_price": exit_signal.exit_price,
                "qty": exit_signal.qty
            })
    
    return None
