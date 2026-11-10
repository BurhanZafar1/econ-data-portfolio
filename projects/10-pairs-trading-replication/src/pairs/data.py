"""Load the raw files written by get_data.py into daily simple return panels."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"


def industry_returns(path: Path = RAW / "ff49_industries_vw_daily.csv.xz") -> pd.DataFrame:
    """Daily value weighted returns (decimal) of the 49 Fama-French industries; missing is NaN."""
    frame = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    frame = frame.where(frame > -99.0)  # French codes missing as -99.99 or -999
    return frame / 100.0


def etf_returns(path: Path = RAW / "sector_etf_adjclose_daily.csv.xz") -> pd.DataFrame:
    """Daily total returns of the nine Select Sector SPDRs from adjusted closes."""
    prices = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    returns = prices.pct_change(fill_method=None).iloc[1:]
    return returns


def stock_returns(path: Path = RAW / "sp500_current_members_returns_bp.csv.xz") -> pd.DataFrame:
    """Daily total returns (decimal) of current S&P 500 members, from each one's first entry."""
    frame = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    return frame / 1e4


def membership(path: Path = RAW / "sp500_membership_intervals.csv") -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["start_date", "end_date"])


def member_on(intervals: pd.DataFrame, columns: pd.Index, date: pd.Timestamp) -> np.ndarray:
    """Boolean mask over columns: ticker was an S&P 500 member on `date` (point in time)."""
    end = intervals["end_date"].fillna(pd.Timestamp.max)
    live = intervals.loc[(intervals["start_date"] <= date) & (end > date), "ticker"]
    return columns.isin(set(live))


def factors_monthly(path: Path = RAW / "ff_factors_monthly.csv") -> pd.DataFrame:
    """Monthly factors in decimals, indexed by month end period."""
    frame = pd.read_csv(path)
    frame.index = pd.PeriodIndex(frame.pop("date").astype(str), freq="M")
    return frame / 100.0


def month_starts(index: pd.DatetimeIndex) -> pd.PeriodIndex:
    """Calendar months present in a daily index."""
    return pd.PeriodIndex(np.unique(index.to_period("M")), freq="M")
