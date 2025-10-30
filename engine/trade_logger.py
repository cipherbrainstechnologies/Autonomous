"""
Trade Logger for comprehensive trade logging to CSV
"""

import csv
import os
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError

from .db import get_session, init_database
from .models import Trade
import pandas as pd


class TradeLogger:
    """
    Handles trade logging to CSV with comprehensive trade information.
    """
    
    def __init__(self, trades_file: str = "logs/trades.csv"):
        """
        Initialize TradeLogger.
        
        Args:
            trades_file: Path to CSV file for storing trades
        """
        self.trades_file = trades_file
        self._ensure_directory_exists()
        self._ensure_header_exists()
    
    def _ensure_directory_exists(self):
        """Ensure logs directory exists."""
        directory = os.path.dirname(self.trades_file)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def _ensure_header_exists(self):
        """Ensure CSV file has header row if it's new."""
        if not os.path.exists(self.trades_file):
            header = [
                'timestamp', 'symbol', 'strike', 'direction', 'order_id',
                'entry', 'sl', 'tp', 'exit', 'pnl', 'status',
                'pre_reason', 'post_outcome', 'quantity'
            ]
            with open(self.trades_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
    
    def log_trade(self, trade: Dict):
        """
        Log a trade to CSV file.
        
        Args:
            trade: Dictionary containing trade information with keys:
                   - symbol: Trading symbol
                   - strike: Strike price
                   - direction: 'CE' or 'PE'
                   - order_id: Broker order ID (optional)
                   - entry: Entry price
                   - sl: Stop loss price
                   - tp: Take profit price
                   - exit: Exit price (optional, can be None for open trades)
                   - pnl: Profit/Loss (optional)
                   - status: Trade status ('pending', 'open', 'closed', 'stopped')
                   - pre_reason: Reason for entering trade
                   - post_outcome: Outcome/reason for exit (optional)
                   - quantity: Number of lots
        """
        # Prepare row data with defaults
        row = {
            'timestamp': trade.get('timestamp', datetime.now().isoformat()),
            'symbol': trade.get('symbol', 'NIFTY'),
            'strike': trade.get('strike', ''),
            'direction': trade.get('direction', ''),
            'order_id': trade.get('order_id', ''),
            'entry': trade.get('entry', ''),
            'sl': trade.get('sl', ''),
            'tp': trade.get('tp', ''),
            'exit': trade.get('exit', ''),
            'pnl': trade.get('pnl', ''),
            'status': trade.get('status', 'open'),
            'pre_reason': trade.get('pre_reason', ''),
            'post_outcome': trade.get('post_outcome', ''),
            'quantity': trade.get('quantity', '')
        }
        
        # Write to CSV
        with open(self.trades_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'symbol', 'strike', 'direction', 'order_id',
                'entry', 'sl', 'tp', 'exit', 'pnl', 'status',
                'pre_reason', 'post_outcome', 'quantity'
            ])
            writer.writerow(row)

        # Also attempt to persist executed trades to Postgres if fields are available
        try:
            self._maybe_write_trade_to_db(trade)
        except Exception:
            # DB persistence is best-effort; CSV remains source of truth if DB unavailable
            pass

    def _maybe_write_trade_to_db(self, trade: Dict):
        """
        Best-effort write of executed trades into Postgres with idempotency.
        Requires minimal fields: org_id, user_id, symbol, side(BUY/SELL), quantity, price, traded_at.
        If not present, this is a no-op.
        """
        org_id = trade.get('org_id')
        user_id = trade.get('user_id')
        if not org_id or not user_id:
            return

        symbol = trade.get('symbol')
        side = trade.get('side') or trade.get('buy_sell')
        # Derive side from direction if needed (CE -> BUY assumed for entry)
        if not side and trade.get('direction'):
            dirv = str(trade.get('direction')).upper()
            side = 'BUY' if dirv in ('BUY', 'CE') else 'SELL'

        quantity = trade.get('quantity')
        price = trade.get('entry') or trade.get('price')
        if price is None or quantity in (None, '') or not symbol or not side:
            return

        try:
            price_num = Decimal(str(price))
        except (InvalidOperation, TypeError):
            return

        order_id = trade.get('order_id') or None
        strategy_id = trade.get('strategy_id') or None
        broker = trade.get('broker') or None

        # traded_at from timestamp if provided
        ts = trade.get('timestamp')
        if isinstance(ts, str):
            try:
                traded_at = datetime.fromisoformat(ts)
            except ValueError:
                traded_at = datetime.utcnow()
        else:
            traded_at = datetime.utcnow()

        # Ensure tables exist in dev environments
        try:
            init_database(create_all=True)
        except Exception:
            pass

        sess_gen = get_session()
        db = next(sess_gen)
        try:
            row = Trade(
                org_id=str(org_id),
                user_id=str(user_id),
                strategy_id=str(strategy_id) if strategy_id else None,
                symbol=str(symbol),
                side=str(side).upper(),
                quantity=int(quantity),
                price=price_num,
                fees=Decimal(str(trade.get('fees', '0')) or '0'),
                order_id=str(order_id) if order_id else None,
                broker=str(broker) if broker else None,
                traded_at=traded_at,
            )
            db.add(row)
            db.commit()
        except IntegrityError:
            db.rollback()
            # Idempotent duplicate; ignore
        except Exception:
            db.rollback()
            raise
        finally:
            try:
                next(sess_gen)
            except StopIteration:
                pass
    
    def get_all_trades(self) -> pd.DataFrame:
        """
        Read all trades from CSV file.
        
        Returns:
            DataFrame with all trade records
        """
        if not os.path.exists(self.trades_file):
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(self.trades_file)
            return df
        except Exception as e:
            print(f"Error reading trades: {e}")
            return pd.DataFrame()
    
    def get_open_trades(self) -> pd.DataFrame:
        """
        Get all open/pending trades.
        
        Returns:
            DataFrame with open trades
        """
        df = self.get_all_trades()
        if df.empty:
            return df
        
        open_statuses = ['open', 'pending']
        return df[df['status'].isin(open_statuses)]
    
    def get_trade_stats(self) -> Dict:
        """
        Calculate trade statistics.
        
        Returns:
            Dictionary with trade statistics
        """
        df = self.get_all_trades()
        
        if df.empty:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0
            }
        
        closed_trades = df[df['status'] == 'closed'].copy()
        
        if closed_trades.empty:
            return {
                'total_trades': len(closed_trades),
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0
            }
        
        # Convert PnL to numeric
        closed_trades['pnl'] = pd.to_numeric(closed_trades['pnl'], errors='coerce')
        
        winning_trades = closed_trades[closed_trades['pnl'] > 0]
        losing_trades = closed_trades[closed_trades['pnl'] < 0]
        
        total_pnl = closed_trades['pnl'].sum()
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if len(closed_trades) > 0 else 0
        
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0.0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0.0
        
        return {
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'total_pnl': float(total_pnl),
            'win_rate': float(win_rate),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss)
        }
    
    def update_trade_exit(self, order_id: str, exit_price: float, pnl: float, outcome: str):
        """
        Update trade with exit information.
        
        Args:
            order_id: Broker order ID
            exit_price: Exit price
            pnl: Profit/Loss
            outcome: Exit reason/outcome
        """
        # Read all trades
        df = self.get_all_trades()
        
        if df.empty:
            return
        
        # Find trade by order_id
        mask = df['order_id'] == order_id
        if not mask.any():
            return
        
        # Update values
        df.loc[mask, 'exit'] = exit_price
        df.loc[mask, 'pnl'] = pnl
        df.loc[mask, 'status'] = 'closed'
        df.loc[mask, 'post_outcome'] = outcome
        
        # Write back to CSV
        df.to_csv(self.trades_file, index=False)

    def import_trades_from_csv(self, file_like) -> Dict:
        """
        Import manual/external trades from an uploaded CSV and merge into trade log.

        The CSV may have varying column names. This method attempts to normalize
        to the expected schema and deduplicates on (timestamp, symbol, strike, direction, quantity).

        Args:
            file_like: Uploaded file-like object from Streamlit uploader

        Returns:
            Dict with keys: {"imported": int, "skipped": int, "total": int}
        """
        try:
            incoming = pd.read_csv(file_like)
        except Exception as e:
            return {"imported": 0, "skipped": 0, "total": 0, "error": str(e)}

        # Normalize columns
        rename_map = {
            'time': 'timestamp',
            'datetime': 'timestamp',
            'symbolname': 'symbol',
            'tradingsymbol': 'symbol',
            'qty': 'quantity',
            'side': 'direction'
        }
        incoming.columns = [c.strip() for c in incoming.columns]
        incoming = incoming.rename(columns={k: v for k, v in rename_map.items() if k in incoming.columns})

        # Ensure all expected columns exist
        expected_cols = ['timestamp','symbol','strike','direction','order_id','entry','sl','tp','exit','pnl','status','pre_reason','post_outcome','quantity']
        for col in expected_cols:
            if col not in incoming.columns:
                incoming[col] = ''

        # Coerce timestamp to string ISO if possible
        try:
            incoming['timestamp'] = pd.to_datetime(incoming['timestamp'], errors='coerce').dt.strftime('%Y-%m-%dT%H:%M:%S')
        except Exception:
            incoming['timestamp'] = incoming['timestamp'].astype(str)

        # Read existing
        existing = self.get_all_trades()
        if existing.empty:
            merged = incoming[expected_cols].copy()
        else:
            merged = pd.concat([existing, incoming[expected_cols]], ignore_index=True)

        before = len(merged)
        merged = merged.drop_duplicates(subset=['timestamp','symbol','strike','direction','quantity'], keep='first')
        after = len(merged)

        # Write back
        merged.to_csv(self.trades_file, index=False)

        return {"imported": len(incoming), "skipped": before + 0 - after, "total": after}


def log_trade(trade: Dict):
    """
    Convenience function for logging a trade.
    
    Args:
        trade: Trade dictionary (see TradeLogger.log_trade for format)
    """
    logger = TradeLogger()
    logger.log_trade(trade)

