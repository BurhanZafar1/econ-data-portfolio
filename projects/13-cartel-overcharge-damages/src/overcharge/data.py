"""Load and validate the Joint Executive Committee (JEC) weekly data.

Units, from Porter (1983, Table 1):
  price     grain rate, dollars per 100 lbs, Chicago to the Atlantic seaboard
  quantity  total grain shipped by JEC members, tons per week
  cartel    1 when the trade press (Railway Review) reported collusion
  lakes     1 when the Great Lakes were open to navigation (a rival route)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "CartelStability.csv"

N_WEEKS = 328
N_SEASONS = 13
LBS_PER_TON = 2000
PRICE_UNIT_LBS = 100

# The 13 four-week periods in calendar order, as labeled in the source file.
SEASON_ORDER = [
    "Jan  1 - Jan 28", "Jan 29 - Feb 25", "Feb 26 - Mar 26", "Mar 27 - Apr 23",
    "Apr 24 - May 21", "May 22 - Jun 18", "Jun 19 - Jul 16", "Jul 17 - Aug 13",
    "Aug 14 - Sep 10", "Sep 11 - Oct  8", "Oct  9 - Nov  5", "Nov  6 - Dec  3",
    "Dec  4 - Dec 31",
]


def load_jec(path: Path = DATA_FILE) -> pd.DataFrame:
    """Read the raw file and return a clean weekly panel with numeric columns."""
    raw = pd.read_csv(path)
    df = pd.DataFrame(
        {
            "week": raw["rownames"].astype(int),
            "price": raw["price"].astype(float),
            "quantity": raw["quantity"].astype(float),
            "cartel": (raw["cartel"] == "yes").astype(int),
            # The source codes "ice" (lakes closed); Porter's LAKES is its complement.
            "lakes": (raw["ice"] == "no").astype(int),
            "season": raw["season"].map({s: i + 1 for i, s in enumerate(SEASON_ORDER)}),
        }
    )
    df["log_price"] = np.log(df["price"])
    df["log_quantity"] = np.log(df["quantity"])
    # Freight revenue in dollars: $/100 lbs times tons times 20 hundredweights per ton.
    df["revenue"] = df["price"] * df["quantity"] * LBS_PER_TON / PRICE_UNIT_LBS
    df["episode"] = (df["cartel"].diff().fillna(0) != 0).cumsum()
    validate(df)
    return df


def validate(df: pd.DataFrame) -> None:
    """Fail loudly if the file is not the 328-week series Porter describes."""
    if len(df) != N_WEEKS:
        raise ValueError(f"expected {N_WEEKS} weeks, found {len(df)}")
    if df["season"].isna().any():
        raise ValueError("unrecognized season label")
    if not df["week"].is_monotonic_increasing:
        raise ValueError("weeks are out of order")
    if (df["price"] <= 0).any() or (df["quantity"] <= 0).any():
        raise ValueError("prices and quantities must be positive")
    if set(df["cartel"].unique()) != {0, 1} or set(df["lakes"].unique()) != {0, 1}:
        raise ValueError("indicator columns must take both values 0 and 1")


def season_dummies(df: pd.DataFrame) -> pd.DataFrame:
    """Twelve season indicators, with season 13 (December) as the base."""
    # A fixed category list keeps all 13 columns even in a subsample missing a season.
    seasons = pd.Categorical(df["season"], categories=range(1, N_SEASONS + 1))
    dummies = pd.get_dummies(seasons, prefix="seas").astype(float).set_axis(df.index)
    return dummies.drop(columns=f"seas_{N_SEASONS}")
