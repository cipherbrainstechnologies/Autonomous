"""
Trade Management and Signal Processing Functions
Implements core trading logic: signal detection, option selection, risk management, and trade execution
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from logzero import logger


@dataclass
class Signal:
    """Signal object containing range and timestamp"""
    range_high: float
    range_low: float
    ts: datetime
    inside_bar_high: Optional[float] = None
    inside_bar_low: Optional[float] = None


@dataclass
class Option:
    """Option contract details"""
    symbol: str
    strike: int
    expiry: datetime
    lot: int = 75
    option_type: Optional[str] = None  # "CE" or "PE"
    trading_symbol: Optional[str] = None
    symbol_token: Optional[str] = None


@dataclass
class Exit:
    """Exit signal for position"""
    reason: str
    exit_price: Optional[float] = None
    quantity: Optional[int] = None
    timestamp: Optional[datetime] = None


def detect_signal_candle(h1: pd.DataFrame) -> Optional[Signal]:
    """
    Detect Inside Bar signal candle pattern in 1-hour timeframe.
    
    An Inside Bar is when a candle is completely contained within the previous candle's range.
    Returns the most recent Inside Bar with its range (from parent candle).
    
    Args:
        h1: DataFrame with 1-hour OHLC data
             Must have columns: ['High', 'Low', 'Open', 'Close', 'Date']
    
    Returns:
        Signal object with range_high, range_low, and timestamp, or None if no signal
    """
    if h1 is None or len(h1) < 2:
        logger.debug("Insufficient data for signal candle detection (need at least 2 candles)")
        return None
    
    # Find Inside Bar patterns
    inside_bars = []
    
    for i in range(2, len(h1)):
        current_high = h1['High'].iloc[i]
        current_low = h1['Low'].iloc[i]
        prev_high = h1['High'].iloc[i-1]
        prev_low = h1['Low'].iloc[i-1]
        
        # Inside bar condition: current candle completely inside previous candle
        if current_high < prev_high and current_low > prev_low:
            inside_bars.append(i)
    
    if not inside_bars:
        logger.debug("No Inside Bar patterns detected")
        return None
    
    # Get the most recent Inside Bar
    latest_idx = inside_bars[-1]
    inside_bar_candle = h1.iloc[latest_idx]
    reference_candle = h1.iloc[latest_idx - 1]
    
    # Extract range from reference candle (the one containing the inside bar)
    range_high = reference_candle['High']
    range_low = reference_candle['Low']
    inside_bar_high = inside_bar_candle['High']
    inside_bar_low = inside_bar_candle['Low']
    
    # Get timestamp
    ts = inside_bar_candle['Date'] if 'Date' in h1.columns else h1.index[latest_idx]
    if hasattr(ts, 'to_pydatetime'):
        ts = ts.to_pydatetime()
    elif isinstance(ts, pd.Timestamp):
        ts = ts.to_pydatetime()
    
    signal = Signal(
        range_high=float(range_high),
        range_low=float(range_low),
        ts=ts,
        inside_bar_high=float(inside_bar_high),
        inside_bar_low=float(inside_bar_low)
    )
    
    logger.info(
        f"Signal candle detected at {ts} | "
        f"Range: {range_low:.2f} - {range_high:.2f} | "
        f"Inside Bar: {inside_bar_low:.2f} - {inside_bar_high:.2f}"
    )
    
    return signal


def breakout_side(h1_close: float, signal: Signal) -> Optional[str]:
    """
    Determine breakout direction based on close price and signal range.
    
    Args:
        h1_close: Current 1-hour close price
        signal: Signal object with range_high and range_low
    
    Returns:
        "CE" for bullish breakout (close > range_high)
        "PE" for bearish breakout (close < range_low)
        None if no breakout
    """
    if signal is None:
        return None
    
    if h1_close > signal.range_high:
        logger.info(f"Bullish breakout: {h1_close:.2f} > {signal.range_high:.2f} (CE)")
        return "CE"
    elif h1_close < signal.range_low:
        logger.info(f"Bearish breakout: {h1_close:.2f} < {signal.range_low:.2f} (PE)")
        return "PE"
    else:
        logger.debug(f"No breakout: {signal.range_low:.2f} <= {h1_close:.2f} <= {signal.range_high:.2f}")
        return None


def eligible_to_trade(context: Dict) -> bool:
    """
    Check if trading is eligible based on filters: gaps, IV, spread, ATR.
    
    Args:
        context: Dictionary containing:
            - 'gap_threshold': float (max allowed gap as % of spot, default 0.5%)
            - 'iv_threshold_min': float (min IV, default 15%)
            - 'iv_threshold_max': float (max IV, default 50%)
            - 'spread_threshold': float (max bid-ask spread as % of mid, default 2%)
            - 'atr_threshold_min': float (min ATR as % of spot, default 0.3%)
            - 'spot': float (current spot price)
            - 'prev_close': float (previous day close)
            - 'current_iv': float (current implied volatility)
            - 'bid': float (current bid price)
            - 'ask': float (current ask price)
            - 'atr': float (Average True Range)
            - 'filters_enabled': Dict with enabled filters
    
    Returns:
        True if eligible to trade, False otherwise
    """
    if context is None:
        return False
    
    filters_enabled = context.get('filters_enabled', {})
    spot = context.get('spot')
    prev_close = context.get('prev_close')
    
    if spot is None or spot <= 0:
        logger.warning("Invalid spot price in context")
        return False
    
    # Gap filter: Check if gap is too large
    if filters_enabled.get('gap', True):
        gap_threshold_pct = context.get('gap_threshold', 0.5)  # 0.5% default
        if prev_close and prev_close > 0:
            gap_pct = abs((spot - prev_close) / prev_close) * 100
            if gap_pct > gap_threshold_pct:
                logger.debug(f"Gap filter failed: {gap_pct:.2f}% > {gap_threshold_pct}%")
                return False
    
    # IV filter: Check if IV is within acceptable range
    if filters_enabled.get('iv', True):
        iv_min = context.get('iv_threshold_min', 15.0)  # 15% min IV
        iv_max = context.get('iv_threshold_max', 50.0)  # 50% max IV
        current_iv = context.get('current_iv')
        
        if current_iv is not None:
            if current_iv < iv_min or current_iv > iv_max:
                logger.debug(f"IV filter failed: {current_iv:.2f}% not in range [{iv_min}, {iv_max}]%")
                return False
    
    # Spread filter: Check bid-ask spread
    if filters_enabled.get('spread', True):
        spread_threshold_pct = context.get('spread_threshold', 2.0)  # 2% default
        bid = context.get('bid')
        ask = context.get('ask')
        
        if bid is not None and ask is not None and bid > 0 and ask > bid:
            mid_price = (bid + ask) / 2
            spread_pct = ((ask - bid) / mid_price) * 100
            if spread_pct > spread_threshold_pct:
                logger.debug(f"Spread filter failed: {spread_pct:.2f}% > {spread_threshold_pct}%")
                return False
    
    # ATR filter: Check if ATR indicates sufficient volatility
    if filters_enabled.get('atr', True):
        atr_min_pct = context.get('atr_threshold_min', 0.3)  # 0.3% min ATR
        atr = context.get('atr')
        
        if atr is not None and spot > 0:
            atr_pct = (atr / spot) * 100
            if atr_pct < atr_min_pct:
                logger.debug(f"ATR filter failed: {atr_pct:.2f}% < {atr_min_pct}%")
                return False
    
    logger.debug("All eligibility filters passed")
    return True


def pick_option(
    symbol: str,
    spot: float,
    side: str,
    broker=None,
    atm_offset: int = 0,
    lot_size: int = 75
) -> Optional[Option]:
    """
    Pick appropriate option contract based on symbol, spot price, and side.
    
    Args:
        symbol: Underlying symbol (e.g., "NIFTY")
        spot: Current spot price
        side: "CE" or "PE"
        broker: Optional broker instance for fetching expiry dates
        atm_offset: Offset from ATM strike (default: 0 = ATM)
        lot_size: Lot size (default: 75 for NIFTY)
    
    Returns:
        Option object with strike, expiry, and lot size
    """
    if side not in ["CE", "PE"]:
        logger.error(f"Invalid side: {side}. Must be 'CE' or 'PE'")
        return None
    
    if spot <= 0:
        logger.error(f"Invalid spot price: {spot}")
        return None
    
    # Calculate strike price (NIFTY strikes are multiples of 50)
    base_strike = round(spot / 50) * 50
    
    if side == "CE":
        strike = base_strike + atm_offset
    else:  # PE
        strike = base_strike - atm_offset
    
    # Get expiry date (typically weekly expiry - Thursday for NIFTY)
    # Default to next Thursday if broker not available
    if broker and hasattr(broker, 'get_option_expiry'):
        try:
            expiry = broker.get_option_expiry(symbol, strike, side)
        except Exception as e:
            logger.warning(f"Error fetching expiry from broker: {e}. Using default.")
            expiry = _get_default_expiry()
    else:
        expiry = _get_default_expiry()
    
    # Generate trading symbol (format may vary by broker)
    # Standard format: NIFTY25JAN26200CE or NIFTY25JAN26200CE for weekly expiry
    trading_symbol = _generate_trading_symbol(symbol, strike, side, expiry)
    
    option = Option(
        symbol=symbol,
        strike=int(strike),
        expiry=expiry,
        lot=lot_size,
        option_type=side,
        trading_symbol=trading_symbol
    )
    
    logger.info(
        f"Selected option: {side} {strike} | "
        f"Expiry: {expiry.strftime('%Y-%m-%d')} | "
        f"Lot: {lot_size} | "
        f"Trading Symbol: {trading_symbol}"
    )
    
    return option


def _get_default_expiry() -> datetime:
    """Get default expiry date (next Thursday for NIFTY weekly expiry)"""
    today = datetime.now()
    days_ahead = 3 - today.weekday()  # Thursday is weekday 3
    if days_ahead <= 0:  # If today is Thursday or later, get next Thursday
        days_ahead += 7
    next_thursday = today + timedelta(days=days_ahead)
    return next_thursday.replace(hour=15, minute=30, second=0, microsecond=0)  # 3:30 PM IST


def _generate_trading_symbol(symbol: str, strike: int, side: str, expiry: datetime) -> str:
    """Generate trading symbol in standard format"""
    # Format: NIFTY + YY + MMM + STRIKE + CE/PE
    # Example: NIFTY25JAN26200CE
    year_short = str(expiry.year)[-2:]
    month_map = {
        1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
        7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'
    }
    month = month_map.get(expiry.month, 'JAN')
    
    # For weekly expiry, might need to adjust format
    # Using standard format for now
    trading_symbol = f"{symbol}{year_short}{month}{strike}{side}"
    return trading_symbol


def compute_lots(acct_risk: float, entry_premium: float, lot_size: int = 75) -> int:
    """
    Compute number of lots based on account risk and entry premium.
    
    Args:
        acct_risk: Maximum risk per trade in rupees (e.g., 5000)
        entry_premium: Entry premium per lot
        lot_size: Lot size (default: 75 for NIFTY)
    
    Returns:
        Number of lots (integer)
    """
    if entry_premium <= 0:
        logger.error(f"Invalid entry premium: {entry_premium}")
        return 0
    
    if acct_risk <= 0:
        logger.error(f"Invalid account risk: {acct_risk}")
        return 0
    
    # Calculate risk per lot (considering stop loss)
    # Assuming initial SL is 35% of entry premium (0.65 * entry)
    sl_pct = 0.35  # 35% stop loss
    risk_per_lot = entry_premium * lot_size * sl_pct
    
    # Calculate number of lots
    lots = int(acct_risk / risk_per_lot) if risk_per_lot > 0 else 0
    
    # Ensure at least 1 lot if account risk allows
    if lots < 1 and acct_risk >= risk_per_lot:
        lots = 1
    
    logger.info(
        f"Computed lots: {lots} | "
        f"Account risk: {acct_risk:.2f} | "
        f"Risk per lot: {risk_per_lot:.2f} | "
        f"Entry premium: {entry_premium:.2f}"
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
    sl = entry_premium * 0.65
    logger.debug(f"Initial SL: {sl:.2f} (65% of entry {entry_premium:.2f})")
    return sl


def update_trailing(
    context: Dict,
    entry_premium: float,
    cur_premium: float,
    atr: Optional[float] = None,
    swings: Optional[Dict] = None,
    iv: Optional[float] = None
) -> float:
    """
    Update trailing stop loss based on context, market conditions, and price movement.
    
    Args:
        context: Dictionary containing:
            - 'trail_points': int (trailing step in points, default: 10)
            - 'initial_sl': float (initial stop loss)
            - 'high_since_entry': float (highest price since entry)
            - 'trail_anchor': float (current trailing anchor)
        entry_premium: Original entry premium
        cur_premium: Current premium price
        atr: Average True Range (optional)
        swings: Dictionary with swing high/low data (optional)
        iv: Current implied volatility (optional)
    
    Returns:
        Updated trailing stop loss price
    """
    # Get initial SL and trailing parameters
    initial_sl_price = context.get('initial_sl', initial_sl(entry_premium))
    trail_points = context.get('trail_points', 10)  # Default 10 points
    high_since_entry = context.get('high_since_entry', entry_premium)
    trail_anchor = context.get('trail_anchor', entry_premium)
    
    # Update high since entry
    if cur_premium > high_since_entry:
        high_since_entry = cur_premium
        context['high_since_entry'] = high_since_entry
    
    # Calculate profit in points
    profit_points = cur_premium - entry_premium
    
    # Only trail if in profit
    if profit_points <= 0:
        # Still at loss or breakeven, use initial SL
        updated_sl = initial_sl_price
        logger.debug(f"No trailing (in loss): SL = {updated_sl:.2f}")
        return updated_sl
    
    # Calculate trailing SL based on trail_points increment
    # Move anchor up when price advances by trail_points
    if cur_premium - trail_anchor >= trail_points:
        increments = int((cur_premium - trail_anchor) // trail_points)
        if increments > 0:
            trail_anchor += increments * trail_points
            context['trail_anchor'] = trail_anchor
    
    # Calculate trailing stop loss
    # Trailing SL = trail_anchor - initial_sl_offset
    initial_sl_offset = entry_premium - initial_sl_price
    updated_sl = trail_anchor - initial_sl_offset
    
    # Ensure trailing SL doesn't go below initial SL
    updated_sl = max(updated_sl, initial_sl_price)
    
    # Optional: Adjust based on ATR, swings, or IV
    if atr and atr > 0:
        # Use ATR-based trailing (more dynamic)
        # Trail by 1.5 * ATR from high
        atr_trail = high_since_entry - (1.5 * atr)
        updated_sl = max(updated_sl, atr_trail)
    
    if swings:
        # Use swing-based trailing
        swing_low = swings.get('swing_low')
        if swing_low and swing_low > initial_sl_price:
            # Use swing low as trailing SL if it's above initial SL
            updated_sl = max(updated_sl, swing_low)
    
    logger.debug(
        f"Trailing SL updated: {updated_sl:.2f} | "
        f"Current premium: {cur_premium:.2f} | "
        f"High since entry: {high_since_entry:.2f} | "
        f"Trail anchor: {trail_anchor:.2f}"
    )
    
    return updated_sl


def time_expiry_exit(
    now: datetime,
    is_expiry_day: bool,
    premium: float,
    position: Dict
) -> Optional[Exit]:
    """
    Check if position should be exited based on expiry day timing.
    
    Args:
        now: Current datetime
        is_expiry_day: Whether today is expiry day
        premium: Current premium price
        position: Position dictionary with:
            - 'entry_price': float
            - 'quantity': int
            - 'expiry': datetime
            - 'side': str ("CE" or "PE")
    
    Returns:
        Exit object if exit should occur, None otherwise
    """
    if not is_expiry_day:
        return None
    
    entry_price = position.get('entry_price', 0)
    quantity = position.get('quantity', 0)
    expiry = position.get('expiry')
    side = position.get('side', 'CE')
    
    if not expiry:
        logger.warning("Expiry date not found in position")
        return None
    
    # Convert expiry to datetime if needed
    if isinstance(expiry, str):
        try:
            expiry = datetime.fromisoformat(expiry)
        except Exception:
            logger.warning(f"Could not parse expiry: {expiry}")
            return None
    
    # Check time-based exit rules for expiry day
    # Exit options on expiry day:
    # 1. Before 3:00 PM if in profit (book profits)
    # 2. At 3:00 PM if still open (avoid exercise risk)
    # 3. Exit immediately if premium < 5% of entry (time decay)
    
    exit_time_early = now.replace(hour=15, minute=0, second=0, microsecond=0)  # 3:00 PM IST
    exit_time_late = expiry.replace(hour=15, minute=15, second=0, microsecond=0)  # 3:15 PM IST (final exit)
    
    # Check if premium has decayed too much (time value erosion)
    premium_decay_threshold = entry_price * 0.05  # 5% of entry
    
    if premium < premium_decay_threshold:
        reason = f"Premium decay on expiry: {premium:.2f} < {premium_decay_threshold:.2f} (5% of entry)"
        logger.info(reason)
        return Exit(
            reason=reason,
            exit_price=premium,
            quantity=quantity,
            timestamp=now
        )
    
    # Exit at 3:00 PM if in profit (book profits before close)
    if now >= exit_time_early and premium > entry_price:
        reason = f"Profit booking on expiry day at 3:00 PM: Premium {premium:.2f} > Entry {entry_price:.2f}"
        logger.info(reason)
        return Exit(
            reason=reason,
            exit_price=premium,
            quantity=quantity,
            timestamp=now
        )
    
    # Final exit at 3:15 PM (15 minutes before market close)
    if now >= exit_time_late:
        reason = f"Mandatory exit on expiry day at 3:15 PM to avoid exercise"
        logger.info(reason)
        return Exit(
            reason=reason,
            exit_price=premium,
            quantity=quantity,
            timestamp=now
        )
    
    return None


def manage_trade_tick(
    position: Dict,
    current_premium: float,
    context: Dict,
    market_data: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Manage trade on each tick: check for exits or modifications.
    
    Args:
        position: Position dictionary with:
            - 'entry_price': float
            - 'quantity': int
            - 'side': str ("CE" or "PE")
            - 'strike': int
            - 'expiry': datetime
            - 'initial_sl': float
            - 'trailing_sl': float
            - 'high_since_entry': float
            - 'trail_anchor': float
        current_premium: Current premium price
        context: Trading context with:
            - 'atr': float
            - 'swings': Dict
            - 'iv': float
            - 'is_expiry_day': bool
            - 'now': datetime
        market_data: Optional market data dictionary
    
    Returns:
        Dictionary with exit/modify action or None:
        {
            'action': 'exit' or 'modify',
            'reason': str,
            'exit_price': float (for exit),
            'new_sl': float (for modify),
            'quantity': int
        }
    """
    if not position or current_premium <= 0:
        return None
    
    entry_price = position.get('entry_price', 0)
    quantity = position.get('quantity', 0)
    
    if entry_price <= 0 or quantity <= 0:
        logger.warning("Invalid position data")
        return None
    
    # Update context with position data
    if 'initial_sl' not in context:
        context['initial_sl'] = position.get('initial_sl', initial_sl(entry_price))
    context.setdefault('high_since_entry', position.get('high_since_entry', entry_price))
    context.setdefault('trail_anchor', position.get('trail_anchor', entry_price))
    
    # Update trailing stop loss
    atr = context.get('atr')
    swings = context.get('swings')
    iv = context.get('iv')
    
    updated_sl = update_trailing(
        context=context,
        entry_premium=entry_price,
        cur_premium=current_premium,
        atr=atr,
        swings=swings,
        iv=iv
    )
    
    # Check initial stop loss
    current_sl = position.get('trailing_sl', context['initial_sl'])
    if updated_sl > current_sl:
        # Trailing SL moved up, modify position
        logger.info(f"Trailing SL updated: {current_sl:.2f} -> {updated_sl:.2f}")
        return {
            'action': 'modify',
            'reason': 'Trailing stop loss updated',
            'new_sl': updated_sl,
            'quantity': quantity
        }
    
    # Check if stop loss is hit
    if current_premium <= updated_sl:
        reason = f"Stop loss hit: {current_premium:.2f} <= {updated_sl:.2f}"
        logger.info(reason)
        return {
            'action': 'exit',
            'reason': reason,
            'exit_price': current_premium,
            'quantity': quantity
        }
    
    # Check expiry day exit
    is_expiry_day = context.get('is_expiry_day', False)
    now = context.get('now', datetime.now())
    
    if is_expiry_day:
        exit_signal = time_expiry_exit(
            now=now,
            is_expiry_day=is_expiry_day,
            premium=current_premium,
            position=position
        )
        if exit_signal:
            return {
                'action': 'exit',
                'reason': exit_signal.reason,
                'exit_price': exit_signal.exit_price,
                'quantity': exit_signal.quantity
            }
    
    # Check profit targets (if configured)
    book1_points = context.get('book1_points', 40)  # Book 50% at +40 points
    book2_points = context.get('book2_points', 54)  # Book remaining at +54 points
    book1_done = position.get('book1_done', False)
    book2_done = position.get('book2_done', False)
    
    if not book1_done and current_premium >= entry_price + book1_points:
        # First profit target hit
        book_qty = int(quantity * 0.5)  # Book 50%
        logger.info(f"Profit target 1 hit: Booking {book_qty} lots")
        return {
            'action': 'partial_exit',
            'reason': f'Profit target 1 hit: {current_premium:.2f} >= {entry_price + book1_points:.2f}',
            'exit_price': current_premium,
            'quantity': book_qty
        }
    
    if not book2_done and current_premium >= entry_price + book2_points:
        # Second profit target hit - exit remaining
        remaining_qty = position.get('remaining_qty', quantity)
        logger.info(f"Profit target 2 hit: Booking remaining {remaining_qty} lots")
        return {
            'action': 'exit',
            'reason': f'Profit target 2 hit: {current_premium:.2f} >= {entry_price + book2_points:.2f}',
            'exit_price': current_premium,
            'quantity': remaining_qty
        }
    
    # No action needed
    return None
