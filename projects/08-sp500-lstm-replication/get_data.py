"""Download daily S&P 500 index data (^GSPC) from the Yahoo Finance chart endpoint.

The 2019 project used pandas_datareader with fix_yahoo_finance, which no longer works.
This script calls the same Yahoo data through its public chart endpoint and saves
data/raw/sp500_daily.csv (December 1979 to the end date below).

Run:  python get_data.py
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent / "data" / "raw" / "sp500_daily.csv"
START = datetime(1979, 12, 1, tzinfo=timezone.utc)
END = datetime(2026, 11, 7, tzinfo=timezone.utc)  # exclusive; last trading day kept is 6 Nov 2026
URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
    "?period1={p1}&period2={p2}&interval=1d&events=history"
)


def download(start: datetime = START, end: datetime = END) -> pd.DataFrame:
    """Return daily OHLCV for ^GSPC between start (inclusive) and end (exclusive)."""
    url = URL.format(p1=int(start.timestamp()), p2=int(end.timestamp()))
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)["chart"]["result"][0]
    quote = payload["indicators"]["quote"][0]
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(payload["timestamp"], unit="s").normalize().date,
            "open": quote["open"],
            "high": quote["high"],
            "low": quote["low"],
            "close": quote["close"],
            "volume": quote["volume"],
        }
    )
    return frame.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)


if __name__ == "__main__":
    data = download()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUT, index=False, float_format="%.6f")
    print(f"Saved {len(data)} rows, {data['date'].iloc[0]} to {data['date'].iloc[-1]}, to {OUT}")
