"""Trading period simulation for a set of pairs (GGR 2006, sections 1.3 to 1.4).

Rule, per pair, with prices re-normalized to 1 at the start of the trading period:
  * open when the normalized price spread moves more than k formation period standard
    deviations away from zero: buy $V of the cheaper leg, short $V of the dearer leg,
    where V is the pair's current capital (payoffs are reinvested; idle cash earns zero);
  * close at the next crossing of the normalized prices; a pair may open again later;
  * close any open position on the last day of the trading period;
  * a security with missing returns is treated as delisted: the position is closed at
    the last available price and the pair stops trading;
  * wait = 1 executes every open and close at the close of the day AFTER the signal.
Positions are marked to market daily (buy and hold within a trade). A proportional
cost `cost` (fraction of notional, per leg, per side) is charged on every open and close.
All decisions at day t use prices up to and including day t only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class TradeResult:
    value: np.ndarray  # T x P daily pair value (capital 1 at the start)
    opened: np.ndarray  # P bool: pair opened at least once
    round_trips: np.ndarray  # P int: completed or forced closes
    days_open: np.ndarray  # P int


def simulate(
    ra: np.ndarray,
    rb: np.ndarray,
    sigma: np.ndarray,
    k: float = 2.0,
    wait: int = 0,
    cost: float = 0.0,
) -> TradeResult:
    """Simulate P pairs over T trading days. ra, rb: T x P daily returns of legs a and b."""
    T, P = ra.shape
    alive_a = ~np.isnan(ra)
    alive_b = ~np.isnan(rb)
    ra = np.nan_to_num(ra)
    rb = np.nan_to_num(rb)
    pa = np.ones(P)
    pb = np.ones(P)
    cash = np.ones(P)
    long_val = np.zeros(P)
    short_val = np.zeros(P)
    pos = np.zeros(P, dtype=int)  # +1 long a short b, -1 long b short a
    pend = np.zeros(P, dtype=int)  # pending action: 0 none, +-1 open, 2 close
    pend_day = np.full(P, -1)
    dead = np.zeros(P, dtype=bool)
    opened = np.zeros(P, dtype=bool)
    trips = np.zeros(P, dtype=int)
    days_open = np.zeros(P, dtype=int)
    value = np.empty((T, P))
    thr = k * sigma

    def close(mask: np.ndarray) -> None:
        cash[mask] += long_val[mask] - short_val[mask] - cost * (long_val[mask] + short_val[mask])
        long_val[mask] = 0.0
        short_val[mask] = 0.0
        pos[mask] = 0
        trips[mask] += 1

    for t in range(T):
        # delisting: a leg without a return today; close at yesterday's value and stop.
        newly_dead = ~dead & ~(alive_a[t] & alive_b[t])
        if newly_dead.any():
            close(newly_dead & (pos != 0))
            pend[newly_dead] = 0
            dead |= newly_dead
        live = ~dead
        # mark open positions to market with today's returns
        is_long_a = live & (pos == 1)
        is_long_b = live & (pos == -1)
        long_val[is_long_a] *= 1.0 + ra[t, is_long_a]
        short_val[is_long_a] *= 1.0 + rb[t, is_long_a]
        long_val[is_long_b] *= 1.0 + rb[t, is_long_b]
        short_val[is_long_b] *= 1.0 + ra[t, is_long_b]
        days_open[live & (pos != 0)] += 1
        pa[live] *= 1.0 + ra[t, live]
        pb[live] *= 1.0 + rb[t, live]
        spread = pa - pb

        # execute actions signalled `wait` days ago (wait=0: signalled today, below)
        if wait > 0:
            due = live & (pend != 0) & (pend_day == t - wait)
            _execute(due, pend, pos, cash, long_val, short_val, opened, cost, close, t == T - 1)

        # new signals from today's close
        flat = live & (pos == 0) & (pend == 0)
        sig_open = flat & (np.abs(spread) > thr)
        direction = np.where(spread < 0, 1, -1)  # a cheap -> long a
        crossed = ((pos == 1) & (spread >= 0)) | ((pos == -1) & (spread <= 0))
        sig_close = live & (pend == 0) & crossed
        pend[sig_open] = direction[sig_open]
        pend[sig_close] = 2
        pend_day[sig_open | sig_close] = t
        if wait == 0:
            due = live & (pend != 0)
            _execute(due, pend, pos, cash, long_val, short_val, opened, cost, close, t == T - 1)

        if t == T - 1:
            close(live & (pos != 0))
        value[t] = cash + long_val - short_val
    return TradeResult(value, opened, trips, days_open)


def _execute(due, pend, pos, cash, long_val, short_val, opened, cost, close, last_day=False) -> None:
    """Run due actions; no new position is opened on the last day (it would close at once)."""
    to_close = due & (pend == 2)
    if to_close.any():
        close(to_close)
    to_open = due & ((pend == 1) | (pend == -1)) & (not last_day)
    if to_open.any():
        cap = cash[to_open]
        long_val[to_open] = cap
        short_val[to_open] = cap
        cash[to_open] -= 2.0 * cost * cap
        pos[to_open] = pend[to_open]
        opened[to_open] = True
    pend[due] = 0
