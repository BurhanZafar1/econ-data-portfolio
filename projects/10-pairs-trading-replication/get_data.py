"""Download every input used by run.py into data/raw (a copy is committed).

Sources (all public, no login):
  * Kenneth R. French Data Library, Dartmouth (Tuck): 49 industry portfolios, daily
    value weighted returns with dividends; monthly Fama-French 3 factors, momentum
    and short term reversal factors.
  * Yahoo Finance chart endpoint: dividend and split adjusted closes of the nine
    original Select Sector SPDR ETFs (listed December 1998) and of current S&P 500
    members.
  * S&P 500 membership history compiled by F. Jamesson (github.com/fja05680/sp500,
    MIT license, file sp500_ticker_start_end.csv, commit pinned below). This is a
    community compilation, not an official S&P file.

Run:  python get_data.py
"""

from __future__ import annotations

import io
import json
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent / "data" / "raw"
FRENCH = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{name}_CSV.zip"
YAHOO = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    "?period1={p1}&period2={p2}&interval=1d&events=div%2Csplit"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
ETFS = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
SP500_COMMIT = "a2430f2af0c79ddf0748e91de11bdeb1616ab5a7"
SP500_URL = f"https://raw.githubusercontent.com/fja05680/sp500/{SP500_COMMIT}/sp500_ticker_start_end.csv"
STOCK_START = datetime(2001, 12, 1, tzinfo=timezone.utc)
ETF_START = datetime(1998, 12, 1, tzinfo=timezone.utc)
ETF_END = datetime(2026, 11, 7, tzinfo=timezone.utc)  # exclusive


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def _french_text(name: str) -> str:
    archive = zipfile.ZipFile(io.BytesIO(_get(FRENCH.format(name=name))))
    return archive.read(archive.namelist()[0]).decode("latin-1")


def _block(text: str, start_marker: str | None, date_len: int) -> pd.DataFrame:
    """Parse the first table after start_marker whose rows begin with a date of date_len digits."""
    lines = text.splitlines()
    i = 0
    if start_marker is not None:
        i = next(k for k, line in enumerate(lines) if line.strip() == start_marker)
    while not lines[i].lstrip().startswith(","):
        i += 1
    header = ["date"] + [c.strip() for c in lines[i].split(",")[1:]]
    rows = []
    for line in lines[i + 1 :]:
        first = line.split(",")[0].strip()
        if not (first.isdigit() and len(first) == date_len):
            break
        rows.append([first] + [float(x) for x in line.split(",")[1:]])
    return pd.DataFrame(rows, columns=header)


def industries() -> pd.DataFrame:
    text = _french_text("49_Industry_Portfolios_daily")
    frame = _block(text, "Average Value Weighted Returns -- Daily", 8)
    frame["date"] = pd.to_datetime(frame["date"], format="%Y%m%d")
    return frame[frame["date"] >= "1961-01-01"].reset_index(drop=True)


def factors_monthly() -> pd.DataFrame:
    ff = _block(_french_text("F-F_Research_Data_Factors"), None, 6)
    mom = _block(_french_text("F-F_Momentum_Factor"), None, 6)
    rev = _block(_french_text("F-F_ST_Reversal_Factor"), None, 6)
    out = ff.merge(mom, on="date").merge(rev, on="date")
    out.columns = [c.strip() for c in out.columns]
    return out


def etf(ticker: str, start: datetime = ETF_START) -> pd.Series:
    url = YAHOO.format(ticker=ticker, p1=int(start.timestamp()), p2=int(ETF_END.timestamp()))
    payload = json.loads(_get(url))["chart"]["result"][0]
    adj = payload["indicators"]["adjclose"][0]["adjclose"]
    dates = pd.to_datetime(payload["timestamp"], unit="s").normalize()
    return pd.Series(adj, index=dates, name=ticker).dropna().groupby(level=0).last()


def membership() -> pd.DataFrame:
    """Membership intervals of every ticker; current members have an empty end_date."""
    return pd.read_csv(io.BytesIO(_get(SP500_URL)))


def stock_returns(tickers: list[str]) -> pd.DataFrame:
    """Daily total returns (from adjusted closes) of the given tickers, Dec 2001 onward."""

    def one(ticker: str) -> pd.Series | None:
        try:
            return etf(ticker.replace(".", "-"), STOCK_START).rename(ticker)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print("failed", ticker, exc)
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        series = [s for s in pool.map(one, tickers) if s is not None]
    prices = pd.concat(series, axis=1).sort_index()
    return prices.pct_change(fill_method=None).iloc[1:]


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    ind = industries()
    ind.to_csv(RAW / "ff49_industries_vw_daily.csv.xz", index=False, float_format="%.2f")
    print("industries", ind.shape, ind["date"].min().date(), ind["date"].max().date())
    fac = factors_monthly()
    fac.to_csv(RAW / "ff_factors_monthly.csv", index=False)
    print("factors", fac.shape, fac["date"].iloc[0], fac["date"].iloc[-1])
    prices = pd.concat([etf(t) for t in ETFS], axis=1)
    prices.index.name = "date"
    prices.to_csv(RAW / "sector_etf_adjclose_daily.csv.xz", float_format="%.6f")
    print("etfs", prices.shape, prices.index.min().date(), prices.index.max().date())
    members = membership()
    members.to_csv(RAW / "sp500_membership_intervals.csv", index=False)
    current = sorted(members.loc[members["end_date"].isna(), "ticker"].unique())
    stocks = stock_returns(current)
    stocks.index.name = "date"
    # Keep returns only from each ticker's first S&P 500 entry date (earlier data are
    # never used) and store whole basis points, so the file stays small. Rounding error
    # is at most 0.5 bp a day and has mean zero.
    first_in = members.groupby("ticker")["start_date"].min()
    for ticker in stocks.columns:
        stocks.loc[stocks.index < pd.Timestamp(first_in[ticker]), ticker] = float("nan")
    stocks.mul(1e4).round(0).to_csv(RAW / "sp500_current_members_returns_bp.csv.xz", float_format="%.0f")
    print("stocks", stocks.shape, stocks.index.min().date(), stocks.index.max().date())
