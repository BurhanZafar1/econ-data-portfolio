"""Six overlapping strategies, one starting each month (GGR 2006, section 1.4).

A strategy forms pairs over 12 months and trades them over the next 6 months. A new
strategy starts every month, so six trade at once; the monthly return of the pairs
portfolio is the average of the active strategies' monthly returns.

committed capital: payoffs divided by the number of pairs selected (investable).
fully invested:   payoffs divided by the number of pairs that open during the trading
                  period. This denominator is only known at the end of the period, so
                  it is reported for comparison with the paper, never as a strategy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from . import formation, trading

Selector = Callable[[np.ndarray], formation.Pairs]


@dataclass
class Config:
    top: int | None = 20  # None = every selected pair
    k: float = 2.0
    wait: int = 0
    cost: float = 0.0
    form_months: int = 12
    trade_months: int = 6
    selector: Selector = field(default=formation.nearest_neighbor_pairs)
    # optional point in time universe: formation start date -> bool mask over columns
    eligible: Callable[[pd.Timestamp], np.ndarray] | None = None


@dataclass
class Result:
    monthly: pd.DataFrame  # committed, fully, n_active by calendar month
    periods: pd.DataFrame  # one row per strategy: pairs, opened, round trips, days open


def run(returns: pd.DataFrame, first_trade: str, last_trade: str, cfg: Config) -> Result:
    """Monthly returns for calendar months first_trade..last_trade (YYYY-MM, inclusive)."""
    months = returns.index.to_period("M")
    values = returns.to_numpy()
    uniq = pd.period_range(months.min(), months.max(), freq="M")
    pos = {m: np.flatnonzero(months == m) for m in uniq}
    first, last = pd.Period(first_trade, "M"), pd.Period(last_trade, "M")
    rows: dict[pd.Period, list[tuple[float, float]]] = {}
    stats = []
    start = first - cfg.form_months - cfg.trade_months + 1
    while start + cfg.form_months <= last:
        f_months = [start + i for i in range(cfg.form_months)]
        t_months = [start + cfg.form_months + i for i in range(cfg.trade_months)]
        if f_months[0] < uniq[0] or t_months[-1] > uniq[-1]:
            start += 1
            continue
        f_idx = np.concatenate([pos[m] for m in f_months])
        t_idx = np.concatenate([pos[m] for m in t_months])
        form = values[f_idx]
        ok = ~np.isnan(form).any(axis=0)  # complete formation data only
        if cfg.eligible is not None:
            ok &= cfg.eligible(returns.index[f_idx[0]])
        cols = np.flatnonzero(ok)
        pairs = cfg.selector(form[:, cols])
        n = len(pairs.a) if cfg.top is None else min(cfg.top, len(pairs.a))
        a, b = cols[pairs.a[:n]], cols[pairs.b[:n]]
        trade = values[t_idx]
        res = trading.simulate(trade[:, a], trade[:, b], pairs.sigma[:n], cfg.k, cfg.wait, cfg.cost)
        committed = res.value.mean(axis=1)
        fully = res.value[:, res.opened].mean(axis=1) if res.opened.any() else np.ones(len(t_idx))
        bounds = np.cumsum([len(pos[m]) for m in t_months]) - 1
        prev_c, prev_f = 1.0, 1.0
        for m, end in zip(t_months, bounds):
            rows.setdefault(m, []).append((committed[end] / prev_c - 1.0, fully[end] / prev_f - 1.0))
            prev_c, prev_f = committed[end], fully[end]
        stats.append(
            {
                "start": t_months[0],
                "n_universe": len(cols),
                "n_pairs": n,
                "n_opened": int(res.opened.sum()),
                "round_trips": float(res.round_trips[res.opened].mean()) if res.opened.any() else 0.0,
                "months_open": float(res.days_open[res.opened].mean() / 21.0) if res.opened.any() else 0.0,
            }
        )
        start += 1
    idx = [m for m in sorted(rows) if first <= m <= last]
    monthly = pd.DataFrame(
        {
            "committed": [np.mean([r[0] for r in rows[m]]) for m in idx],
            "fully": [np.mean([r[1] for r in rows[m]]) for m in idx],
            "n_active": [len(rows[m]) for m in idx],
        },
        index=pd.PeriodIndex(idx, freq="M"),
    )
    return Result(monthly, pd.DataFrame(stats))
