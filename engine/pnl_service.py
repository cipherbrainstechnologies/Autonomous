from __future__ import annotations

from collections import deque, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .db import get_session
from .models import Trade


def _fifo_realized_pnl(trades: List[Trade]) -> Decimal:
    """
    Compute realized P&L using FIFO across a list of trades for a single symbol.
    Assumes trades are sorted by traded_at ascending.
    BUY increases inventory; SELL reduces using FIFO.
    """
    inventory: deque[Tuple[int, Decimal]] = deque()
    realized = Decimal("0")

    for t in trades:
        qty = int(t.quantity)
        price = Decimal(t.price)
        if str(t.side).upper() == "BUY":
            inventory.append((qty, price))
        else:  # SELL
            sell_qty = qty
            while sell_qty > 0 and inventory:
                lot_qty, lot_price = inventory[0]
                used = min(sell_qty, lot_qty)
                realized += (Decimal(price) - Decimal(lot_price)) * Decimal(used)
                sell_qty -= used
                lot_qty -= used
                if lot_qty == 0:
                    inventory.popleft()
                else:
                    inventory[0] = (lot_qty, lot_price)
            # If short selling beyond inventory, treat remaining as against zero-cost (conservative)
            # or ignore. Here we ignore extra for safety.
    return realized


def compute_realized_pnl(org_id: str, user_id: str, start: Optional[datetime] = None, end: Optional[datetime] = None) -> Dict:
    """
    Realized P&L for a tenant over optional date range using FIFO per symbol.
    """
    sess_gen = get_session()
    db = next(sess_gen)
    try:
        stmt = select(Trade).where(Trade.org_id == org_id, Trade.user_id == user_id)
        if start:
            stmt = stmt.where(Trade.traded_at >= start)
        if end:
            stmt = stmt.where(Trade.traded_at <= end)
        stmt = stmt.order_by(Trade.symbol.asc(), Trade.traded_at.asc(), Trade.id.asc())
        rows = list(db.execute(stmt).scalars())

        by_symbol: Dict[str, List[Trade]] = defaultdict(list)
        for r in rows:
            by_symbol[r.symbol].append(r)

        total = Decimal("0")
        symbol_breakdown: Dict[str, str] = {}
        for sym, ts in by_symbol.items():
            realized = _fifo_realized_pnl(ts)
            symbol_breakdown[sym] = f"{realized:.2f}"
            total += realized

        return {
            "realized_pnl": float(total),
            "by_symbol": symbol_breakdown,
        }
    finally:
        try:
            next(sess_gen)
        except StopIteration:
            pass


def pnl_timeseries(org_id: str, user_id: str) -> List[Dict]:
    """
    Realized P&L per day based on trade executions (approximation): sum(SELL) - sum(BUY) per day per matched FIFO is heavy.
    For a quick approximation, net cash flow per day can be shown; detailed FIFO per day would re-run FIFO per boundary.
    Here we compute net cash flow per day as a proxy.
    """
    sess_gen = get_session()
    db = next(sess_gen)
    try:
        day_col = func.date(Trade.traded_at)
        buy_flow = (
            db.query(day_col.label("d"), func.sum(Trade.price * Trade.quantity).label("amt"))
            .filter(Trade.org_id == org_id, Trade.user_id == user_id, Trade.side == "BUY")
            .group_by(day_col)
            .all()
        )
        sell_flow = (
            db.query(day_col.label("d"), func.sum(Trade.price * Trade.quantity).label("amt"))
            .filter(Trade.org_id == org_id, Trade.user_id == user_id, Trade.side == "SELL")
            .group_by(day_col)
            .all()
        )
        buys = {str(d): Decimal(amt or 0) for d, amt in buy_flow}
        sells = {str(d): Decimal(amt or 0) for d, amt in sell_flow}
        days = sorted(set(buys.keys()) | set(sells.keys()))
        series: List[Dict] = []
        for d in days:
            series.append({"date": d, "net_cash_flow": float(sells.get(d, 0) - buys.get(d, 0))})
        return series
    finally:
        try:
            next(sess_gen)
        except StopIteration:
            pass


