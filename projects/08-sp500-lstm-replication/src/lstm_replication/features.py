"""Features and label exactly as in the original notebook (section 4.2).

For each look back window of w weeks (5 trading days per week), with daily log return r:
  return_w  = sum of r over the last 5w days
  vol_w     = standard deviation of r over the last 5w days times sqrt(5w)
  volume_w  = mean daily volume over the last 5w days
Label for day t: 1 if r(t+1) + ... + r(t+21) > 0, else 0.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

WINDOWS_WEEKS: tuple[int, ...] = (1, 2, 3, 4) + tuple(range(8, 81, 4))  # 23 windows
DAYS_PER_WEEK = 5
HORIZON = 21  # trading days in the label

RETURN_COLS = [f"ret_{w}w" for w in WINDOWS_WEEKS]
VOL_COLS = [f"vol_{w}w" for w in WINDOWS_WEEKS]
VOLUME_COLS = [f"volume_{w}w" for w in WINDOWS_WEEKS]

# The paper numbers its feature sets 1 = volatility, 2 = return, 3 = volume.
FEATURE_SETS: dict[int, list[str]] = {
    1: VOL_COLS,
    2: RETURN_COLS,
    3: VOLUME_COLS,
    4: RETURN_COLS + VOL_COLS,  # notebook column order: returns then volatilities
    5: VOL_COLS + VOLUME_COLS,
    6: RETURN_COLS + VOLUME_COLS,
    7: RETURN_COLS + VOL_COLS + VOLUME_COLS,
}
MODEL_NAMES: dict[int, str] = {
    1: "Volatility",
    2: "Return",
    3: "Volume",
    4: "Volatility + return",
    5: "Volatility + volume",
    6: "Return + volume",
    7: "All three",
}


def log_returns(close: pd.Series) -> pd.Series:
    """Daily log return ln(P_t / P_{t-1}); the first value is NaN."""
    return np.log(close / close.shift(1))


def forward_return(r: pd.Series, horizon: int = HORIZON) -> pd.Series:
    """Sum of the next `horizon` daily log returns, r(t+1) + ... + r(t+horizon)."""
    return r.shift(-horizon).rolling(horizon).sum()


def build(frame: pd.DataFrame, horizon: int = HORIZON) -> pd.DataFrame:
    """69 features, the forward return and the binary label, rows with any gap dropped."""
    r = log_returns(frame["close"])
    out: dict[str, pd.Series] = {}
    for w in WINDOWS_WEEKS:
        out[f"ret_{w}w"] = r.rolling(DAYS_PER_WEEK * w).sum()
    for w in WINDOWS_WEEKS:
        days = DAYS_PER_WEEK * w
        out[f"vol_{w}w"] = r.rolling(days).std() * np.sqrt(days)
    for w in WINDOWS_WEEKS:
        out[f"volume_{w}w"] = frame["volume"].astype(float).rolling(DAYS_PER_WEEK * w).mean()
    out["fwd_return"] = forward_return(r, horizon)
    table = pd.DataFrame(out, index=frame.index).dropna()
    table["label"] = (table["fwd_return"] > 0).astype(int)
    return table
