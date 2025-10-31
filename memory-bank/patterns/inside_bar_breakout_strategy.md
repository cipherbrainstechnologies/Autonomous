# Inside Bar + Breakout Strategy Pattern

## Pattern Overview

The Inside Bar + Breakout strategy is a structured approach for trading NIFTY Index Options that combines consolidation pattern detection with momentum breakout confirmation.

## Intent / Use Case

- **Primary Use**: Detect consolidation patterns (Inside Bars) in 1-hour timeframe
- **Confirmation**: Wait for volume-confirmed breakout on 15-minute timeframe
- **Execution**: Enter trades when breakout occurs with defined risk-reward ratios
- **Risk Management**: Fixed stop loss and take profit based on configurable parameters

## Strategy Logic Flow

### 1. Inside Bar Detection (1H Timeframe)
- Scans 1-hour candles for Inside Bar patterns
- Inside Bar: A candle completely contained within the previous candle's range
- Pattern: `current_high < prev_high AND current_low > prev_low`
- Stores the most recent Inside Bar for range marking

### 2. Range Marking
- Extracts high and low from the candle **before** the Inside Bar
- This range (range_high, range_low) becomes the breakout levels

### 3. Breakout Confirmation (15m Timeframe)
- Monitors last 5 candles on 15-minute timeframe
- Checks each candle (oldest to newest) for breakout
- **Bullish Breakout (CE)**: Close > range_high AND Volume > threshold
- **Bearish Breakout (PE)**: Close < range_low AND Volume > threshold
- Volume threshold = Average volume of last 5 candles × multiplier

### 4. Strike Selection
- ATM (At The Money) based on current NIFTY price
- Strike rounded to nearest 50 (NIFTY strikes are multiples of 50)
- Configurable offset via `atm_offset` parameter

### 5. Entry, SL, TP Calculation
- **Entry**: Current option price (fetched from broker)
- **Stop Loss**: Entry - sl_points (configurable, default 30)
- **Take Profit**: Entry + (sl_points × rr_ratio) (default 1.8)

## Configuration Parameters

```yaml
strategy:
  type: inside_bar
  sl: 30              # Stop Loss in points
  rr: 1.8             # Risk-Reward Ratio
  atm_offset: 0        # Strike offset from ATM (0 = ATM, positive = OTM for calls)
```

## Code Structure

### Core Functions (engine/strategy_engine.py)

1. **detect_inside_bar(data_1h)**
   - Returns list of indices where Inside Bars are detected
   - Requires at least 2 candles of historical data

2. **confirm_breakout(data_15m, range_high, range_low)**
   - Checks last 5 candles for breakout
   - Returns "CE", "PE", or None
   - Validates volume spike requirement

3. **calculate_strike_price(current_price, direction, atm_offset)**
   - Calculates option strike based on current NIFTY price
   - Rounds to nearest 50

4. **calculate_sl_tp_levels(entry_price, sl_points, rr_ratio)**
   - Calculates Stop Loss and Take Profit levels
   - Returns tuple (stop_loss, take_profit)

5. **check_for_signal(data_1h, data_15m, config)**
   - Main signal detection function
   - Combines all logic into single workflow
   - Returns signal dictionary or None

## When to Use

- **Market Conditions**: Range-bound markets with clear consolidation periods
- **Timeframes**: 1H for pattern detection, 15m for entry confirmation
- **Volume Requirement**: Markets with sufficient volume for reliable confirmation
- **Risk Tolerance**: Traders comfortable with defined risk-reward ratios

## When NOT to Use

- **High Volatility Without Patterns**: Choppy markets without clear consolidation
- **Low Volume Periods**: Markets where volume confirmation is unreliable
- **News Events**: Major announcements that can cause false breakouts
- **Market Open (First 30 min)**: If `avoid_open_range` filter is enabled

## Associated Risks

1. **False Breakouts**: Breakout may reverse quickly after entry
   - **Mitigation**: Volume confirmation required

2. **Incomplete Candles**: Using incomplete candles can cause false signals
   - **Mitigation**: System filters out incomplete candles before analysis

3. **Range Selection**: Wrong range (from incorrect Inside Bar) leads to bad entries
   - **Mitigation**: Uses most recent Inside Bar for consistency

4. **Option Pricing**: Entry price estimation may differ from actual option price
   - **Mitigation**: System fetches actual option price from broker API when available

## Integration Points

- **MarketDataProvider**: Fetches and aggregates OHLC data for 1H and 15m timeframes
- **SignalHandler**: Validates signals and manages signal lifecycle
- **BrokerConnector**: Executes trades and fetches option prices
- **TradeLogger**: Logs all signals and trades to CSV
- **PositionMonitor**: Manages open positions with SL/TP tracking

## Example Signal Output

```python
{
    'direction': 'CE',          # Call option (bullish)
    'strike': 26200,            # Strike price
    'entry': 150.50,            # Entry price (option premium)
    'sl': 120.50,               # Stop Loss (entry - 30)
    'tp': 204.50,               # Take Profit (entry + 54)
    'range_high': 26250,        # Inside Bar range high
    'range_low': 26200,         # Inside Bar range low
    'reason': 'Inside Bar breakout on CE side with volume confirmation',
    'timestamp': '2025-01-30T10:45:00',
    'status': 'pending'
}
```

## Testing

The strategy can be tested with:
- Historical backtesting via `backtest_engine.py`
- Paper trading mode (execute signals without real orders)
- Live mode with real broker integration

## References

- Strategy Engine: `engine/strategy_engine.py`
- Signal Handler: `engine/signal_handler.py`
- Configuration: `config/config.yaml`

