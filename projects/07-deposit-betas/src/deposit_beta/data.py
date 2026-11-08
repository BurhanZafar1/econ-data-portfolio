"""Build one monthly table of the federal funds rate and FDIC national deposit rates.

All series come from FRED (Federal Reserve Bank of St. Louis), which republishes the
FDIC national rates. The FDIC changed its method in April 2021, so there are two
families of series:

* 2009-05 to 2021-03: weekly simple averages of posted rates on non-jumbo
  (under $100,000) accounts across branches. We average the weeks in each month.
* 2021-04 onward: monthly averages of rates paid by insured banks and credit
  unions, weighted by market share of domestic deposits (FDIC FIL-24-2021).
  These are published to 0.01 percentage points.

The two families are never spliced in levels. Each row carries an ``era`` label, and
the month-to-month change that crosses the method break is marked invalid.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PRODUCTS: tuple[str, ...] = ("checking", "savings", "money_market", "cd_12m")

PRODUCT_LABELS: dict[str, str] = {
    "checking": "Interest checking",
    "savings": "Savings",
    "money_market": "Money market",
    "cd_12m": "12-month CD",
}

# FRED series id for each product, by FDIC method era.
SERIES_2009: dict[str, str] = {
    "checking": "ICNRNJ",
    "savings": "SAVNRNJ",
    "money_market": "MMNRNJ",
    "cd_12m": "CD12NRNJ",
}
SERIES_2021: dict[str, str] = {
    "checking": "ICNDR",
    "savings": "SNDR",
    "money_market": "MMNDR",
    "cd_12m": "NDR12MCD",
}
POLICY_SERIES = "FEDFUNDS"
ALL_SERIES: tuple[str, ...] = (POLICY_SERIES, *SERIES_2009.values(), *SERIES_2021.values())

ERA_2009 = "fdic_2009_method"
ERA_2021 = "fdic_2021_method"


def read_fred_csv(path: Path) -> pd.Series:
    """Read a fredgraph.csv download into a float Series indexed by date."""
    frame = pd.read_csv(path)
    date_col, value_col = frame.columns[0], frame.columns[1]
    values = pd.to_numeric(frame[value_col], errors="coerce")  # FRED writes '.' for missing
    series = pd.Series(values.to_numpy(), index=pd.to_datetime(frame[date_col]), name=value_col)
    return series.dropna()


def to_monthly_mean(series: pd.Series, min_obs: int = 3) -> pd.Series:
    """Average weekly observations within each calendar month.

    Months with fewer than ``min_obs`` weekly readings (the partial first month of a
    series) are dropped so that every monthly value is a full-month average.
    """
    month = series.index.to_period("M")
    grouped = series.groupby(month)
    monthly = grouped.mean()[grouped.count() >= min_obs]
    monthly.index.name = "month"
    return monthly


def to_month_index(series: pd.Series) -> pd.Series:
    """Re-index a series already at monthly frequency by calendar month."""
    out = series.copy()
    out.index = series.index.to_period("M")
    out.index.name = "month"
    return out


def build_monthly_panel(raw_dir: Path) -> pd.DataFrame:
    """Return one row per month with the funds rate, four deposit rates and the era."""
    load = {sid: read_fred_csv(raw_dir / f"{sid}.csv") for sid in ALL_SERIES}

    old = pd.DataFrame({p: to_monthly_mean(load[sid]) for p, sid in SERIES_2009.items()})
    old["era"] = ERA_2009
    new = pd.DataFrame({p: to_month_index(load[sid]) for p, sid in SERIES_2021.items()})
    new["era"] = ERA_2021
    if not old.index.intersection(new.index).empty:
        raise ValueError("FDIC method eras overlap; expected a clean break")

    deposits = pd.concat([old, new]).sort_index()
    deposits = deposits.dropna(subset=list(PRODUCTS))
    fedfunds = to_month_index(load[POLICY_SERIES]).rename("fedfunds")
    panel = deposits.join(fedfunds, how="inner")
    panel = panel[["era", "fedfunds", *PRODUCTS]]
    if not panel.index.is_monotonic_increasing or panel.index.has_duplicates:
        raise ValueError("monthly index is not unique and increasing")
    return panel


def add_changes(panel: pd.DataFrame) -> pd.DataFrame:
    """Add month-on-month changes, with deposit changes across the era break set to NaN.

    The funds rate is one continuous series, so its change is always valid.
    """
    out = panel.copy()
    full_months = pd.period_range(out.index.min(), out.index.max(), freq="M")
    if len(full_months) != len(out):
        raise ValueError("monthly panel has gaps; changes would span more than one month")
    out["d_fedfunds"] = out["fedfunds"].diff()
    same_era = out["era"].eq(out["era"].shift())
    for product in PRODUCTS:
        out[f"d_{product}"] = out[product].diff().where(same_era)
    return out
