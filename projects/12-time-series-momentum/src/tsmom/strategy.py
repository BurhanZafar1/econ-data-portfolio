"""Ex ante volatility (paper eq. 1), monthly returns and TSMOM portfolios (eq. 5)."""

from __future__ import annotations

import numpy as np
import pandas as pd

CENTER_OF_MASS = 60  # days, so delta / (1 - delta) = 60
ANNUALIZE = 261
TARGET_VOL = 0.40
MIN_DAYS_FOR_VOL = 60
MIN_DAYS_IN_MONTH = 10


def ewma_vol(daily: pd.Series, com: float = CENTER_OF_MASS) -> pd.Series:
    """Annualized ex ante volatility from exponentially weighted squared demeaned returns.

    sigma^2_t = 261 * sum_i (1 - delta) delta^i (r_{t-1-i} - rbar_t)^2 with delta = com / (1 + com).
    The value stamped on day t uses returns up to and including day t; it is only ever
    applied to returns after t.
    """
    r = daily.dropna()
    var = r.ewm(com=com, adjust=True, min_periods=MIN_DAYS_FOR_VOL).var(bias=True)
    return np.sqrt(ANNUALIZE * var)


def monthly_panel(daily: dict[str, pd.Series]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Monthly compounded excess returns and month end ex ante volatility per instrument."""
    rets, vols = {}, {}
    for name, r in daily.items():
        r = r.dropna()
        g = r.groupby(r.index.to_period("M"))
        m = g.apply(lambda x: float(np.prod(1.0 + x.to_numpy()) - 1.0))
        m[g.size() < MIN_DAYS_IN_MONTH] = np.nan
        rets[name] = m
        vols[name] = ewma_vol(r).groupby(r.index.to_period("M")).last()
    ret = pd.DataFrame(rets).sort_index()
    vol = pd.DataFrame(vols).reindex(ret.index)
    return ret, vol


def trailing_return(monthly: pd.DataFrame, k: int) -> pd.DataFrame:
    """Compounded return over the k months ending in month t (needs all k months)."""
    growth = np.log1p(monthly)
    return np.expm1(growth.rolling(k, min_periods=k).sum())


def expanding_vol(daily: pd.Series) -> pd.Series:
    """Annualized volatility from all daily returns up to each day (no volatility timing)."""
    r = daily.dropna()
    return np.sqrt(ANNUALIZE * r.expanding(min_periods=MIN_DAYS_FOR_VOL).var())


def positions(monthly: pd.DataFrame, vol: pd.DataFrame, k: int = 12, h: int = 1, target: float = TARGET_VOL,
              scaled: bool = True, signal: str = "sign") -> pd.DataFrame:
    """Position held over month t+1, stamped at month t (formed with data up to t only).

    With holding period h the direction is the average of the h most recent signals
    (formed at t, t-1, ..., t-h+1), and the whole position is sized by the current
    volatility, as the paper rescales every position each month (section 3.2).
    """
    if signal == "sign":
        direction = np.sign(trailing_return(monthly, k))
    elif signal == "long":
        direction = trailing_return(monthly, k) * 0.0 + 1.0  # same availability as the signal
    else:
        raise ValueError(signal)
    if h > 1:
        direction = direction.rolling(h, min_periods=h).mean()
    size = target / vol if scaled else 1.0
    return direction * size


def strategy_returns(monthly: pd.DataFrame, pos: pd.DataFrame) -> pd.DataFrame:
    """Per instrument return in month t+1 of the position stamped at t (eq. 5)."""
    return pos.shift(1) * monthly


def portfolio(inst_returns: pd.DataFrame, classes: dict[str, str] | None = None, cls: str | None = None) -> pd.Series:
    """Equal weighted average across the instruments available that month (the 1/S_t of eq. 5)."""
    frame = inst_returns
    if cls is not None:
        frame = frame[[c for c in frame.columns if classes[c] == cls]]
    return frame.mean(axis=1, skipna=True).dropna()


def turnover(pos: pd.DataFrame) -> pd.Series:
    """Average absolute change in notional per instrument per month (units of capital).

    Entering or leaving the sample is not counted as trading.
    """
    change = (pos - pos.shift(1)).abs()
    return change.mean(axis=1, skipna=True).dropna()


def net_of_costs(gross: pd.Series, pos: pd.DataFrame, cost_per_unit: float) -> pd.Series:
    """Subtract cost_per_unit (decimal, per unit of notional traded) times turnover.

    The trade at the end of month t is charged to the month t+1 return it creates.
    """
    t = turnover(pos).shift(1).reindex(gross.index).fillna(0.0)
    return gross - cost_per_unit * t
