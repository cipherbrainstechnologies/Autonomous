from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from sqlalchemy import select

from .db import get_session
from .models import Trade
from .pnl_service import compute_realized_pnl


def analyze_trades(org_id: str, user_id: str, lookback_days: int = 30) -> Dict:
    """
    Lightweight analysis over recent trades.
    Returns aggregate metrics suitable for UI display.
    """
    since = datetime.utcnow() - timedelta(days=lookback_days)
    sess_gen = get_session()
    db = next(sess_gen)
    try:
        rows = list(
            db.execute(
                select(Trade).where(
                    Trade.org_id == org_id,
                    Trade.user_id == user_id,
                    Trade.traded_at >= since,
                ).order_by(Trade.traded_at.desc())
            ).scalars()
        )

        total = len(rows)
        buys = sum(1 for r in rows if r.side == "BUY")
        sells = total - buys

        avg_price = float((sum(Decimal(r.price) for r in rows) / total)) if total else 0.0

        realized = compute_realized_pnl(org_id, user_id)

        symbols = {}
        for r in rows:
            symbols[r.symbol] = symbols.get(r.symbol, 0) + 1

        top_symbols = sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "window_days": lookback_days,
            "total_trades": total,
            "buy_trades": buys,
            "sell_trades": sells,
            "avg_trade_price": avg_price,
            "realized_pnl": realized.get("realized_pnl", 0.0),
            "top_symbols": top_symbols,
        }
    finally:
        try:
            next(sess_gen)
        except StopIteration:
            pass


