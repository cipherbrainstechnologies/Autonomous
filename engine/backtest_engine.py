"""
Backtest Engine for historical strategy testing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from engine.strategy_engine import detect_inside_bar, confirm_breakout, calculate_sl_tp_levels


class BacktestEngine:
    """
    Backtesting framework with trade simulation and result calculation.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize BacktestEngine with configuration.
        
        Args:
            config: Configuration dictionary with strategy parameters
        """
        self.config = config
        self.trades = []
        self.equity_curve = []
    
    def run_backtest(
        self,
        data_1h: pd.DataFrame,
        data_15m: pd.DataFrame,
        initial_capital: float = 100000.0
    ) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            data_1h: Historical 1-hour OHLC data
            data_15m: Historical 15-minute OHLCV data aligned with 1h data
            initial_capital: Starting capital
        
        Returns:
            Dictionary with backtest results
        """
        self.trades = []
        self.equity_curve = [initial_capital]
        current_capital = initial_capital
        
        strategy_config = {
            'sl': self.config.get('strategy', {}).get('sl', 30),
            'rr': self.config.get('strategy', {}).get('rr', 1.8)
        }
        
        lot_size = self.config.get('lot_size', 75)
        
        # Detect all Inside Bars first
        inside_bars = detect_inside_bar(data_1h)
        
        if not inside_bars:
            return self._generate_results(initial_capital, current_capital)
        
        # Process each Inside Bar pattern
        for inside_bar_idx in inside_bars:
            if inside_bar_idx < 2:
                continue
            
            # Get range from Inside Bar
            range_high = data_1h['High'].iloc[inside_bar_idx - 1]
            range_low = data_1h['Low'].iloc[inside_bar_idx - 1]
            
            # Find corresponding 15m data after Inside Bar
            inside_bar_time = data_1h.index[inside_bar_idx]
            
            # Get 15m data after Inside Bar
            future_15m = data_15m[data_15m.index > inside_bar_time]
            
            if len(future_15m) < 5:
                continue
            
            # Check for breakout in next few 15m candles
            max_lookahead = min(20, len(future_15m))  # Check next 20 candles max
            
            for i in range(max_lookahead):
                window_15m = future_15m.iloc[:i+1]
                
                # Confirm breakout
                direction = confirm_breakout(window_15m, range_high, range_low)
                
                if direction is None:
                    continue
                
                # Entry signal found
                entry_candle = window_15m.iloc[-1]
                entry_price = entry_candle['Close']  # Simplified: use NIFTY price
                
                # Calculate option entry price (simplified: using intrinsic value estimate)
                if direction == 'CE':
                    option_entry = max(0, entry_price - (data_15m['Close'].iloc[-1] // 50 * 50))
                else:
                    option_entry = max(0, ((data_15m['Close'].iloc[-1] // 50 * 50) - entry_price))
                
                # Calculate SL and TP
                sl_points = strategy_config['sl']
                rr_ratio = strategy_config['rr']
                stop_loss, take_profit = calculate_sl_tp_levels(
                    option_entry,
                    sl_points,
                    rr_ratio
                )
                
                # Simulate trade execution
                trade_result = self._simulate_trade(
                    entry_candle,
                    future_15m.iloc[i:],
                    option_entry,
                    stop_loss,
                    take_profit,
                    direction,
                    lot_size
                )
                
                if trade_result:
                    trade_result['entry_time'] = entry_candle.name
                    self.trades.append(trade_result)
                    
                    # Update capital
                    pnl = trade_result.get('pnl', 0)
                    current_capital += pnl
                    self.equity_curve.append(current_capital)
                    
                    # Only take one trade per Inside Bar
                    break
        
        return self._generate_results(initial_capital, current_capital)
    
    def _simulate_trade(
        self,
        entry_candle: pd.Series,
        future_data: pd.DataFrame,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        direction: str,
        lot_size: int
    ) -> Optional[Dict]:
        """
        Simulate a trade from entry to exit.
        
        Args:
            entry_candle: Entry candle data
            future_data: Future price data after entry
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            direction: 'CE' or 'PE'
            lot_size: Number of lots
        
        Returns:
            Trade result dictionary or None
        """
        if len(future_data) == 0:
            return None
        
        # Check each candle for SL or TP hit
        for idx, candle in future_data.iterrows():
            high = candle['High']
            low = candle['Low']
            close = candle['Close']
            
            # Simplified: check if option price hits SL or TP
            # In reality, would need to calculate option prices from underlying
            
            # For CE: price increases when underlying increases
            # For PE: price increases when underlying decreases
            
            if direction == 'CE':
                # Call option: profit if underlying goes up
                if high >= take_profit:
                    exit_price = take_profit
                    exit_reason = 'TP_HIT'
                    pnl = (exit_price - entry_price) * lot_size
                    break
                elif low <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'SL_HIT'
                    pnl = (exit_price - entry_price) * lot_size
                    break
            else:  # PE
                # Put option: profit if underlying goes down
                if low <= take_profit:
                    exit_price = take_profit
                    exit_reason = 'TP_HIT'
                    pnl = (exit_price - entry_price) * lot_size
                    break
                elif high >= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'SL_HIT'
                    pnl = (exit_price - entry_price) * lot_size
                    break
        else:
            # No exit: use last candle close
            exit_price = close
            exit_reason = 'TIME_EXIT'
            pnl = (exit_price - entry_price) * lot_size
        
        return {
            'direction': direction,
            'entry': entry_price,
            'exit': exit_price,
            'sl': stop_loss,
            'tp': take_profit,
            'pnl': pnl,
            'exit_reason': exit_reason,
            'exit_time': future_data.index[-1],
            'quantity': lot_size
        }
    
    def _generate_results(self, initial_capital: float, final_capital: float) -> Dict:
        """
        Generate backtest results summary.
        
        Args:
            initial_capital: Starting capital
            final_capital: Ending capital
        
        Returns:
            Results dictionary
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'initial_capital': initial_capital,
                'final_capital': final_capital,
                'return_pct': 0.0,
                'trades': []
            }
        
        df_trades = pd.DataFrame(self.trades)
        
        winning_trades = df_trades[df_trades['pnl'] > 0]
        losing_trades = df_trades[df_trades['pnl'] < 0]
        
        total_pnl = df_trades['pnl'].sum()
        win_rate = (len(winning_trades) / len(df_trades) * 100) if len(df_trades) > 0 else 0
        
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0.0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0.0
        
        max_drawdown = self._calculate_max_drawdown()
        
        return {
            'total_trades': len(df_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'total_pnl': float(total_pnl),
            'win_rate': float(win_rate),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'max_drawdown': float(max_drawdown),
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'return_pct': ((final_capital - initial_capital) / initial_capital * 100) if initial_capital > 0 else 0.0,
            'equity_curve': self.equity_curve,
            'trades': self.trades
        }
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve."""
        if len(self.equity_curve) < 2:
            return 0.0
        
        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max * 100
        
        return float(abs(np.min(drawdown)))


def run_backtest(data: pd.DataFrame, strategy_params: Dict) -> Dict:
    """
    Convenience function to run backtest.
    
    Args:
        data: Historical OHLC data
        strategy_params: Strategy parameters dictionary
    
    Returns:
        Backtest results dictionary
    """
    engine = BacktestEngine(strategy_params)
    return engine.run_backtest(data, data, initial_capital=100000.0)

