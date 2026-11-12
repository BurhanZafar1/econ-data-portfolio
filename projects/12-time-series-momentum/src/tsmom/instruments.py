"""Daily excess returns of the public substitutes for the paper's futures.

Each function returns simple daily excess returns indexed by the instrument's own
trading dates. Nothing here looks at future data: the return on day t uses prices or
yields of days t-1 and t only, and futures roll dates follow the exchange calendar
rule applied to the trading days in the data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ROLL_WINDOW = 5  # trading days before last trade in which the next contract is held


# ---------------------------------------------------------------- bonds


def par_bond_price(coupon: np.ndarray, maturity: float, yld: np.ndarray) -> np.ndarray:
    """Price per 1 face of a semiannual bond with the given annual coupon and yield (decimals)."""
    coupon = np.asarray(coupon, dtype=float)
    yld = np.asarray(yld, dtype=float)
    n = int(round(2 * maturity))
    v = 1.0 / (1.0 + yld / 2.0)
    annuity = np.where(np.abs(yld) < 1e-12, n, (1.0 - v**n) / np.where(np.abs(yld) < 1e-12, 1.0, yld / 2.0))
    return coupon / 2.0 * annuity + v**n


def modified_duration_par(yld: float, maturity: float) -> float:
    """Closed form modified duration of a par bond (coupon = yield), semiannual."""
    n = 2 * maturity
    return (1.0 - (1.0 + yld / 2.0) ** (-n)) / yld


def bond_excess_returns(yields: pd.Series, short: pd.Series, maturity: float) -> pd.Series:
    """Constant maturity bond excess return from yields in percent.

    Each day the position is a par bond bought at yesterday's yield, repriced at today's
    yield, plus yesterday's yield minus the short rate accrued over the calendar days
    elapsed (the carry of a futures position financed at the short rate). Roll down is
    ignored.
    """
    frame = pd.DataFrame({"y": yields / 100.0, "s": short / 100.0}).dropna()
    y0, y1 = frame["y"].shift(1), frame["y"]
    s0 = frame["s"].shift(1)
    days = frame.index.to_series().diff().dt.days
    price = par_bond_price(y0.to_numpy(), maturity, y1.to_numpy()) - 1.0
    carry = (y0 - s0) * days / 365.0
    return (pd.Series(price, index=frame.index) + carry).dropna()


# ---------------------------------------------------------------- futures rolls


def last_trade_dates(trading_days: pd.DatetimeIndex, rule: str) -> pd.DatetimeIndex:
    """NYMEX last trading day of each contract, using the data's own trading days.

    rule "CL": three business days before the 25th calendar day of the month before
    delivery (if the 25th is not a business day, three business days before the last
    business day preceding the 25th).
    rule "NG": three business days before the first calendar day of the delivery month.
    rule "HO": last business day of the month before delivery.
    """
    days = pd.DatetimeIndex(trading_days).sort_values()
    out = []
    for _, month_days in pd.Series(days, index=days).groupby(days.to_period("M")):
        md = pd.DatetimeIndex(month_days.values)
        if rule == "CL":
            anchor = md[md.day <= 25]
            if len(anchor) == 0:
                continue
            pos = days.get_loc(anchor[-1])  # the 25th, or the last business day before it
            if pos >= 3:
                out.append(days[pos - 3])
        elif rule == "NG":
            out.append(md[-3] if len(md) >= 3 else md[0])
        elif rule == "HO":
            out.append(md[-1])
        else:
            raise ValueError(rule)
    return pd.DatetimeIndex(out)


def rolled_futures_returns(c1: pd.Series, c2: pd.Series, rule: str, window: int = ROLL_WINDOW) -> pd.Series:
    """Excess return of holding the nearby contract and rolling to the next one early.

    The position is in contract 1 except in the `window` trading days up to and
    including its last trading day, when it is in contract 2. On the first day after
    expiry, yesterday's contract 2 is today's contract 1, so the return is C1_t / C2_t-1.
    A futures return is already an excess return (no cash is invested).
    """
    frame = pd.DataFrame({"c1": c1, "c2": c2}).dropna()
    # Rows with a non-positive price stay in the calendar (April 20, 2020: the expiring
    # May crude contract settled at -37.63 while this position was already in June).
    days = frame.index
    ltd = last_trade_dates(days, rule)
    pos = days.get_indexer(ltd)
    pos = pos[pos >= 0]
    in_window = np.zeros(len(days), dtype=bool)
    after_expiry = np.zeros(len(days), dtype=bool)
    for p in pos:
        in_window[max(0, p - window + 1) : p + 1] = True
        if p + 1 < len(days):
            after_expiry[p + 1] = True
    c1v, c2v = frame["c1"].to_numpy(), frame["c2"].to_numpy()
    r = np.full(len(days), np.nan)
    for t in range(1, len(days)):
        if in_window[t]:
            r[t] = c2v[t] / c2v[t - 1] - 1.0  # in contract 2 since the close before the window
        elif after_expiry[t]:
            r[t] = c1v[t] / c2v[t - 1] - 1.0  # yesterday's contract 2 is today's contract 1
        else:
            r[t] = c1v[t] / c1v[t - 1] - 1.0
    r[~np.isfinite(r)] = np.nan
    if np.any((c1v <= 0) & ~in_window):
        raise ValueError("a non-positive price falls outside the roll window")
    return pd.Series(r, index=days).dropna()


# ---------------------------------------------------------------- equities and currencies


def price_returns(prices: pd.Series) -> pd.Series:
    """Simple returns between consecutive valid closes."""
    p = prices.dropna()
    p = p[p > 0]
    return (p / p.shift(1) - 1.0).dropna()


def roll_date_check(c1: pd.Series, c2: pd.Series, rule: str, offset: int = 0, min_spread: float = 0.03) -> float:
    """Share of rolls where C1 on (roll day + offset) is closer to the previous day's C2 than to C1.

    Only months whose contract 1 to 2 spread exceeds min_spread are informative. If the
    rule dates are right, the share peaks at offset 0.
    """
    f = pd.DataFrame({"c1": c1, "c2": c2}).dropna()
    f = f[(f > 0).all(axis=1)]
    l1, l2 = np.log(f["c1"].to_numpy()), np.log(f["c2"].to_numpy())
    p = f.index.get_indexer(last_trade_dates(f.index, rule))
    p = p[(p >= 3) & (p + 4 < len(f))]
    q = p + 1 + offset
    big = np.abs(l2[q - 1] - l1[q - 1]) > min_spread
    return float(np.mean((np.abs(l1[q] - l2[q - 1]) < np.abs(l1[q] - l1[q - 1]))[big]))
