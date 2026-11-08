"""Cycle (cumulative) deposit betas: deposit rate change divided by funds rate change.

This is the measure bank treasurers and analysts quote: over a whole tightening or
easing cycle, what share of the move in the policy rate reached depositors.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Cycle:
    """A policy cycle measured from the month before the first move to ``end``.

    ``end`` is the last month before the Fed reversed direction (or the last month
    of the FDIC series), so the window includes any drift in deposit rates while
    the funds rate was on hold. ``cycle_table`` also reports the beta measured at
    the month the Fed finished moving, as a check on the choice of end month.
    """

    name: str
    direction: str  # "hike" or "cut"
    base: str  # YYYY-MM, month before the first move
    end: str  # YYYY-MM, last month before the next reversal (or end of the FDIC series)


# Dates read off the monthly FEDFUNDS series (see README). Each window stays inside
# one FDIC method era, so no window crosses the April 2021 break.
CYCLES: tuple[Cycle, ...] = (
    Cycle("2015-2018 hikes", "hike", "2015-11", "2019-07"),
    Cycle("2019-2020 cuts", "cut", "2019-07", "2021-03"),
    Cycle("2022-2023 hikes", "hike", "2022-02", "2024-08"),
    Cycle("2024-2025 cuts", "cut", "2024-08", "2026-08"),
)


def cycle_beta(base_deposit: float, end_deposit: float, base_ff: float, end_ff: float) -> float:
    """Return (change in deposit rate) / (change in funds rate)."""
    d_ff = end_ff - base_ff
    if abs(d_ff) < 1e-9:
        raise ValueError("funds rate did not change over the window")
    return (end_deposit - base_deposit) / d_ff


def cycle_table(panel: pd.DataFrame, products: tuple[str, ...], cycles: tuple[Cycle, ...] = CYCLES) -> pd.DataFrame:
    """One row per cycle and product with start and end levels and the cycle beta."""
    rows = []
    for cycle in cycles:
        base, end = pd.Period(cycle.base, "M"), pd.Period(cycle.end, "M")
        if panel.loc[base, "era"] != panel.loc[end, "era"]:
            raise ValueError(f"{cycle.name} crosses the FDIC method break")
        for product in products:
            rows.append(
                {
                    "cycle": cycle.name,
                    "direction": cycle.direction,
                    "base": cycle.base,
                    "end": cycle.end,
                    "product": product,
                    "ff_base": panel.loc[base, "fedfunds"],
                    "ff_end": panel.loc[end, "fedfunds"],
                    "deposit_base": panel.loc[base, product],
                    "deposit_end": panel.loc[end, product],
                    "beta": cycle_beta(
                        panel.loc[base, product],
                        panel.loc[end, product],
                        panel.loc[base, "fedfunds"],
                        panel.loc[end, "fedfunds"],
                    ),
                }
            )
    table = pd.DataFrame(rows)
    table["last_move"] = [last_move_month(panel, c.base, c.end) for c in cycles for _ in products]
    table["beta_at_last_move"] = [
        cycle_beta(panel.loc[base, p], panel.loc[last, p], panel.loc[base, "fedfunds"], panel.loc[last, "fedfunds"])
        for base, last, p in zip(
            table["base"].map(lambda m: pd.Period(m, "M")),
            table["last_move"].map(lambda m: pd.Period(m, "M")),
            table["product"],
        )
    ]
    table["ff_change"] = table["ff_end"] - table["ff_base"]
    table["deposit_change"] = table["deposit_end"] - table["deposit_base"]
    return table


def last_move_month(panel: pd.DataFrame, base: str, end: str, tolerance: float = 0.05) -> str:
    """First month in the window when the funds rate was within ``tolerance`` of its end level.

    This is when the Fed finished moving; the gap to ``end`` is the hold period.
    """
    window = panel.loc[pd.Period(base, "M") : pd.Period(end, "M"), "fedfunds"]
    reached = window[(window - window.iloc[-1]).abs() <= tolerance]
    return str(reached.index[0])


def beta_path(panel: pd.DataFrame, product: str, base: str, end: str, min_ff_move: float = 0.25) -> pd.Series:
    """Cumulative beta month by month after ``base``.

    Months where the funds rate has moved less than ``min_ff_move`` points since the
    base are left blank, because a ratio over a tiny denominator is noise.
    """
    window = panel.loc[pd.Period(base, "M") : pd.Period(end, "M")]
    d_ff = window["fedfunds"] - window["fedfunds"].iloc[0]
    d_dep = window[product] - window[product].iloc[0]
    path = (d_dep / d_ff).where(d_ff.abs() >= min_ff_move)
    return path.replace([np.inf, -np.inf], np.nan)
