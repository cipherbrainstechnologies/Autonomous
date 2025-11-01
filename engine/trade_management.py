"""Utility functions and state helpers for live trade management.

This module builds on top of the Inside Bar breakout strategy by providing
higher-level helpers to evaluate signal candles, determine breakout side,
run trade filters, pick option contracts, size positions, manage trailing
stops, and make exit decisions during trade management ticks.

The functions exported here are intentionally procedural to keep them easy
to integrate with existing runners or background jobs. Minimal shared state
is stored via helper setters so that `manage_trade_tick()` can operate
without long argument lists while still being explicit about trade state and
market snapshots.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from logzero import logger

from engine.strategy_engine import detect_inside_bar


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


DEFAULT_LOT_SIZE = int(os.getenv("NIFTY_OPTION_LOT_SIZE", "75"))


@dataclass
class Signal:
    """Represents an actionable Inside Bar breakout range."""

    range_high: float
    range_low: float
    timestamp: datetime
    inside_index: int
    parent_index: int
    direction: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Option:
    """Represents an option contract selected for trading."""

    symbol: str
    strike: int
    expiry: date
    side: str  # CE or PE
    lot_size: int = DEFAULT_LOT_SIZE
    tradingsymbol: Optional[str] = None
    underlying_spot: Optional[float] = None

    def __post_init__(self):
        self.side = self.side.upper()
        if self.side not in {"CE", "PE"}:
            raise ValueError(f"Unsupported option side '{self.side}'. Use 'CE' or 'PE'.")


@dataclass
class ExitDecision:
    """Represents an exit instruction determined by risk/time rules."""

    action: str
    reason: str
    price: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeDecision:
    """Represents a trade management action (exit or modification)."""

    action: str  # e.g., EXIT, MODIFY
    reason: str
    timestamp: datetime
    price: Optional[float] = None
    modifications: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeState:
    """Current trade state tracked between ticks."""

    option: Option
    signal: Signal
    entry_premium: float
    stop_loss: float
    target: Optional[float] = None
    direction: str = "CE"
    is_expiry_day: bool = False
    trade_context: Dict[str, Any] = field(default_factory=dict)
    swings: List[float] = field(default_factory=list)


@dataclass
class TradeSnapshot:
    """Latest market snapshot used during a tick."""

    timestamp: datetime
    premium: float
    atr: Optional[float] = None
    iv: Optional[float] = None
    spot: Optional[float] = None


# ---------------------------------------------------------------------------
# Internal module state (set via helper setters before calling manage_trade_tick)
# ---------------------------------------------------------------------------


_CURRENT_TRADE_STATE: Optional[TradeState] = None
_CURRENT_SNAPSHOT: Optional[TradeSnapshot] = None


def set_trade_state(state: TradeState) -> None:
    """Register the baseline trade state for subsequent ticks."""

    global _CURRENT_TRADE_STATE
    _CURRENT_TRADE_STATE = state
    logger.debug(
        "Trade state set | option=%s strike=%s entry=%.2f stop=%.2f target=%s",
        state.option.symbol,
        state.option.strike,
        state.entry_premium,
        state.stop_loss,
        state.target,
    )


def update_trade_snapshot(snapshot: TradeSnapshot) -> None:
    """Capture the latest market snapshot before running a tick."""

    global _CURRENT_SNAPSHOT
    _CURRENT_SNAPSHOT = snapshot
    logger.debug(
        "Snapshot updated | time=%s premium=%.2f atr=%s iv=%s",
        snapshot.timestamp.isoformat(),
        snapshot.premium,
        snapshot.atr,
        snapshot.iv,
    )


# ---------------------------------------------------------------------------
# Core helpers requested by the user
# ---------------------------------------------------------------------------


def detect_signal_candle(h1: pd.DataFrame) -> Optional[Signal]:
    """
    Detect an Inside Bar signal candle on 1-hour data.

    Returns the most recent valid signal with range high/low sourced from the
    parent candle (as per the Inside Bar breakout rules).
    """

    if h1 is None or len(h1) < 3:
        logger.debug("detect_signal_candle: insufficient 1H data provided")
        return None

    inside_bars = detect_inside_bar(h1)
    if not inside_bars:
        logger.debug("detect_signal_candle: no inside bar found")
        return None

    latest_idx = inside_bars[-1]
    if latest_idx <= 0:
        logger.debug("detect_signal_candle: inside bar index without parent candle")
        return None

    inside_bar = h1.iloc[latest_idx]
    parent_bar = h1.iloc[latest_idx - 1]

    timestamp = inside_bar.get("Date")
    if pd.isna(timestamp):
        timestamp = h1.index[latest_idx] if latest_idx < len(h1.index) else datetime.now()

    timestamp = pd.to_datetime(timestamp)
    if isinstance(timestamp, pd.Timestamp):
        if timestamp.tzinfo is not None:
            timestamp = timestamp.tz_convert("Asia/Kolkata").tz_localize(None)
        timestamp = timestamp.to_pydatetime()

    signal = Signal(
        range_high=float(parent_bar["High"]),
        range_low=float(parent_bar["Low"]),
        timestamp=timestamp,
        inside_index=int(latest_idx),
        parent_index=int(latest_idx - 1),
        metadata={
            "inside_high": float(inside_bar["High"]),
            "inside_low": float(inside_bar["Low"]),
        },
    )

    logger.debug(
        "Signal detected | time=%s range=[%.2f, %.2f] inside_idx=%d",
        signal.timestamp,
        signal.range_low,
        signal.range_high,
        signal.inside_index,
    )
    return signal


def breakout_side(h1_close: Union[pd.DataFrame, pd.Series, float, int], signal: Optional[Signal]) -> Optional[str]:
    """Determine breakout direction relative to the signal range."""

    if signal is None:
        return None

    if isinstance(h1_close, pd.DataFrame):
        price = float(h1_close["Close"].iloc[-1]) if not h1_close.empty else None
    elif isinstance(h1_close, pd.Series):
        price = float(h1_close.iloc[-1])
    else:
        price = float(h1_close)

    if price is None:
        logger.debug("breakout_side: could not derive price from input")
        return None

    if price > signal.range_high:
        signal.direction = "CE"
        return "CE"
    if price < signal.range_low:
        signal.direction = "PE"
        return "PE"

    return None


def eligible_to_trade(context: Optional[Dict[str, Any]]) -> bool:
    """Run pre-trade filters (gap, IV, spread, ATR)."""

    if not context:
        return True

    gap = context.get("gap_percent")
    gap_threshold = context.get("gap_threshold", 0.6)
    allow_gap = context.get("allow_gap_trading", False)
    if gap is not None and not allow_gap and abs(gap) > gap_threshold:
        logger.info("Trade blocked: gap %.2f%% exceeds threshold %.2f%%", gap, gap_threshold)
        return False

    iv = context.get("iv")
    iv_limits = context.get("iv_limits", (10.0, 35.0))
    if iv is not None:
        iv_low, iv_high = iv_limits
        if not (iv_low <= iv <= iv_high):
            logger.info("Trade blocked: IV %.2f outside band [%0.2f, %0.2f]", iv, iv_low, iv_high)
            return False

    spread = context.get("spread")
    max_spread = context.get("max_spread", 3.0)
    if spread is not None and spread > max_spread:
        logger.info("Trade blocked: spread %.2f > %.2f", spread, max_spread)
        return False

    atr = context.get("atr")
    atr_limits = context.get("atr_limits", (5.0, 40.0))
    if atr is not None:
        atr_min, atr_max = atr_limits
        if atr < atr_min or atr > atr_max:
            logger.info("Trade blocked: ATR %.2f not within [%0.2f, %0.2f]", atr, atr_min, atr_max)
            return False

    return True


def pick_option(symbol: str, spot: float, side: str, lot: int = DEFAULT_LOT_SIZE, expiry: Optional[date] = None) -> Option:
    """
    Select an option contract based on spot and direction.

    Strikes are rounded to the nearest 50. Expiry defaults to the next weekly
    Thursday (India market convention) unless provided explicitly.
    """

    if spot <= 0:
        raise ValueError("Spot price must be positive to pick option strike")

    strike = int(round(spot / 50.0) * 50)
    side = side.upper()
    if side not in {"CE", "PE"}:
        raise ValueError("Option side must be 'CE' or 'PE'")

    if expiry is None:
        expiry = _next_weekly_expiry(datetime.now().date())

    option = Option(
        symbol=symbol,
        strike=strike,
        expiry=expiry,
        side=side,
        lot_size=lot,
        underlying_spot=spot,
    )

    logger.debug(
        "Option picked | symbol=%s strike=%d expiry=%s side=%s lot=%d",
        option.symbol,
        option.strike,
        option.expiry.isoformat(),
        option.side,
        option.lot_size,
    )
    return option


def compute_lots(acct_risk: float, entry_premium: float, lot_size: int = DEFAULT_LOT_SIZE) -> int:
    """Compute lot count based on account risk and entry premium."""

    if acct_risk <= 0 or entry_premium <= 0:
        return 0

    stop_price = initial_sl(entry_premium)
    risk_per_lot = (entry_premium - stop_price) * lot_size

    if risk_per_lot <= 0:
        logger.warning("compute_lots: non-positive risk per lot (entry=%.2f stop=%.2f)", entry_premium, stop_price)
        return 0

    lots = int(acct_risk // risk_per_lot)
    return max(lots, 0)


def initial_sl(entry_premium: float) -> float:
    """Initial stop loss priced at 35% risk (retain 65% of premium)."""

    if entry_premium <= 0:
        raise ValueError("Entry premium must be positive for SL computation")
    return round(entry_premium * 0.65, 2)


def update_trailing(
    context: Optional[Dict[str, Any]],
    entry_premium: float,
    cur_premium: float,
    atr: Optional[float],
    swings: Optional[List[float]],
    iv: Optional[float],
) -> float:
    """Return the updated trailing stop based on ATR, swings, and IV."""

    base_stop = initial_sl(entry_premium)
    cfg = (context or {}).get("trailing", {})
    current_stop = float((context or {}).get("current_sl", base_stop))
    current_stop = max(current_stop, base_stop)

    if cur_premium <= entry_premium:
        return current_stop

    activation = cfg.get("activate_after", max(5.0, atr or 0))
    if cur_premium - entry_premium < activation:
        return current_stop

    atr_multiplier = cfg.get("atr_multiplier", 1.5)
    min_buffer = cfg.get("min_buffer", max(entry_premium * 0.15, 5.0))
    iv_widen = cfg.get("iv_widen_factor", 0.1)
    min_gap = cfg.get("min_gap", 1.0)

    atr_buffer = (atr or 0) * atr_multiplier
    if atr_buffer <= 0:
        atr_buffer = min_buffer
    else:
        atr_buffer = max(atr_buffer, min_buffer)

    candidate = cur_premium - atr_buffer

    if swings:
        try:
            swing_level = float(swings[-1])
            swing_buffer = cfg.get("swing_buffer", 1.0)
            candidate = max(candidate, swing_level - swing_buffer)
        except (TypeError, ValueError):
            logger.debug("update_trailing: unable to use swings for trailing stop")

    if iv is not None:
        iv_mid = cfg.get("iv_reference", 18.0)
        if iv > iv_mid:
            candidate -= (iv - iv_mid) * iv_widen

    candidate = min(candidate, cur_premium - min_gap)
    new_stop = max(current_stop, candidate)

    return round(max(new_stop, base_stop), 2)


def time_expiry_exit(
    now: datetime,
    is_expiry_day: bool,
    premium: float,
    position: Optional[Dict[str, Any]],
) -> Optional[ExitDecision]:
    """Return exit decision if time-based or premium-based exit triggers fire."""

    if premium <= 0:
        return ExitDecision(action="EXIT", reason="premium_zero", price=0.0, timestamp=now)

    rules = (position or {}).get("exit_rules", {})

    expiry_cutoff = _parse_time(rules.get("expiry_cutoff"), time(15, 10))
    general_cutoff = _parse_time(rules.get("eod_cutoff"), time(15, 20))
    min_premium = float(rules.get("min_premium", 5.0))

    if is_expiry_day:
        if now.time() >= expiry_cutoff:
            return ExitDecision("EXIT", "expiry_cutoff", premium, now)
        if premium <= min_premium:
            return ExitDecision("EXIT", "expiry_intrinsic_exhausted", premium, now)
    else:
        if now.time() >= general_cutoff:
            return ExitDecision("EXIT", "eod_cutoff", premium, now)

    return None


def manage_trade_tick() -> Optional[TradeDecision]:
    """
    Execute one management tick using the registered trade state and snapshot.

    Returns a TradeDecision instructing the caller to exit or modify orders, or
    None if no action is required.
    """

    if _CURRENT_TRADE_STATE is None or _CURRENT_SNAPSHOT is None:
        logger.debug("manage_trade_tick: state or snapshot missing")
        return None

    state = _CURRENT_TRADE_STATE
    snap = _CURRENT_SNAPSHOT

    # Time-based exits
    exit_decision = time_expiry_exit(
        now=snap.timestamp,
        is_expiry_day=state.is_expiry_day,
        premium=snap.premium,
        position=state.trade_context,
    )
    if exit_decision:
        return TradeDecision(
            action=exit_decision.action,
            reason=exit_decision.reason,
            timestamp=exit_decision.timestamp,
            price=exit_decision.price,
        )

    # Hard stop / target checks
    if snap.premium <= state.stop_loss:
        return TradeDecision(
            action="EXIT",
            reason="stop_loss_hit",
            timestamp=snap.timestamp,
            price=snap.premium,
        )

    if state.target is not None and snap.premium >= state.target:
        return TradeDecision(
            action="EXIT",
            reason="target_hit",
            timestamp=snap.timestamp,
            price=snap.premium,
        )

    # Trailing stop update
    new_stop = update_trailing(
        context=state.trade_context,
        entry_premium=state.entry_premium,
        cur_premium=snap.premium,
        atr=snap.atr,
        swings=state.swings,
        iv=snap.iv,
    )

    if new_stop > state.stop_loss:
        state.stop_loss = new_stop
        if state.trade_context is not None:
            state.trade_context["current_sl"] = new_stop
        logger.debug("Trailing stop moved to %.2f", new_stop)
        return TradeDecision(
            action="MODIFY",
            reason="trailing_update",
            timestamp=snap.timestamp,
            price=snap.premium,
            modifications={"stop_loss": new_stop},
        )

    return None


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _next_weekly_expiry(ref_date: date) -> date:
    """Return the next weekly expiry (Thursday) including the current week."""

    weekday_thursday = 3  # Monday=0
    days_ahead = (weekday_thursday - ref_date.weekday()) % 7
    if days_ahead == 0:
        # If already Thursday, choose same day if before close else next week
        days_ahead = 0
    expiry = ref_date + timedelta(days=days_ahead)
    if expiry == ref_date and datetime.now().time() >= time(15, 30):
        expiry = expiry + timedelta(days=7)
    return expiry


def _parse_time(value: Any, default: time) -> time:
    """Parse a value into time, falling back to default."""

    if isinstance(value, time):
        return value

    if isinstance(value, str):
        for fmt in ("%H:%M", "%H%M", "%I:%M%p", "%I:%M %p"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue

    return default


__all__ = [
    "Signal",
    "Option",
    "ExitDecision",
    "TradeDecision",
    "TradeState",
    "TradeSnapshot",
    "set_trade_state",
    "update_trade_snapshot",
    "detect_signal_candle",
    "breakout_side",
    "eligible_to_trade",
    "pick_option",
    "compute_lots",
    "initial_sl",
    "update_trailing",
    "time_expiry_exit",
    "manage_trade_tick",
]

