
# 🧠 Angel One Strategy: 1H + 15M Candles with Retry Logic

## 📌 Goal

You are implementing a **live trading strategy** using Angel One's broker API. The strategy must:

- Pull **1 Hour** and **15 Minute** candle data reliably.
- Work around intermittent API failures (`AB1004` errors).
- Skip the strategy cycle if complete candles are not available.
- Automatically retry failed `/getCandleData` requests.

---

## 🔁 Resilient Candle Fetching: `fetch_historical_candles_with_retry.py`

```python
import requests
import time
import logging

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def fetch_historical_candles_with_retry(url, headers, body):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=body, headers=headers)
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get("status") and json_data.get("data"):
                    return json_data["data"]
                else:
                    logger.warning(f"[Retry {attempt}] Empty or invalid data: {json_data}")
            else:
                logger.warning(f"[Retry {attempt}] HTTP {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"[Retry {attempt}] Exception occurred: {e}")

        time.sleep(RETRY_DELAY)

    logger.error("All retries failed. Returning None.")
    return None
```

---

## 🧠 Example Usage in `market_data.py`

```python
from fetch_historical_candles_with_retry import fetch_historical_candles_with_retry

def get_candles(symboltoken, interval, from_dt, to_dt):
    url = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"

    headers = {
        'X-PrivateKey': 'API_KEY',
        'Authorization': 'Bearer AUTH_TOKEN',
        'Accept': 'application/json',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': '127.0.0.1',
        'X-ClientPublicIP': '106.193.147.98',
        'X-MACAddress': '10:68:38:b1:cb:86',
        'X-UserType': 'USER',
        'Content-Type': 'application/json'
    }

    payload = {
        "exchange": "NSE",
        "symboltoken": symboltoken,
        "interval": interval,
        "fromdate": from_dt.strftime("%Y-%m-%d %H:%M"),
        "todate": to_dt.strftime("%Y-%m-%d %H:%M")
    }

    candles = fetch_historical_candles_with_retry(url, headers, payload)
    return candles
```

---

## ⏳ Strategy Safeguard in `live_runner.py`

```python
candles_1h = get_candles("99926000", "ONE_HOUR", from_dt, to_dt)
if not candles_1h or len(candles_1h) < 20:
    logger.warning("Skipping cycle: insufficient 1H data")
    return

candles_15m = get_candles("99926000", "FIFTEEN_MINUTE", from_dt, to_dt)
if not candles_15m or len(candles_15m) < 3:
    logger.warning("Skipping cycle: insufficient 15M data")
    return
```

---

## 📚 Notes from Angel One Docs

- Endpoint: `/rest/secure/angelbroking/historical/v1/getCandleData`
- Supported Intervals: `ONE_MINUTE`, `FIFTEEN_MINUTE`, `ONE_HOUR`, etc.
- Max Days per Request:
  - 1-minute: 30 days
  - 15-minute: 200 days
  - 1-hour: 400 days
- Date Format: `"yyyy-MM-dd HH:mm"`

---

## ✅ What Cursor AI Should Do

1. Create `fetch_historical_candles_with_retry.py` with retry logic.
2. Update `market_data.py` to use retry wrapper.
3. Patch `live_runner.py` to **skip strategy cycles** if data is missing.
4. Add test call example to verify API success/failure handling.

---

_Last updated: 2025-10-31 07:20_
