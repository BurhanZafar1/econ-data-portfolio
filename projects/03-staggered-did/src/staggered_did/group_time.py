"""Group time average treatment effects of Callaway and Sant'Anna (2021).

ATT(g, t) compares the outcome change from base year to year t for cohort g
with the same change in a clean comparison group. Post treatment cells use
base year g - 1. Pre treatment cells use year t - 1 by default, giving one year
placebo effects, or g - 1 with the universal base, which lines them up with a
regression event study that omits event time -1. With covariates the comparison group's change is predicted by
outcome regression, the method called "reg" in the did package.

Each ATT comes with its influence function: the contribution of each unit to
the estimate's sampling error. Standard errors, clustering, the bootstrap and
every aggregation are then simple matrix operations on these columns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from staggered_did.panel import Panel

ControlGroup = Literal["never", "notyet"]
BasePeriod = Literal["varying", "universal"]


@dataclass(frozen=True)
class GroupTimeResult:
    """ATT(g, t) table plus an N by K matrix of influence functions."""

    table: pd.DataFrame
    influence: np.ndarray
    panel: Panel


def outcome_regression_did(
    change: np.ndarray, treated: np.ndarray, control: np.ndarray, x: np.ndarray
) -> tuple[float, np.ndarray]:
    """Two group DiD with outcome regression and its influence function.

    change is each unit's outcome change, x includes the constant. With a
    constant alone this is the plain difference in mean changes.
    """
    x_control = x[control]
    beta, *_ = np.linalg.lstsq(x_control, change[control], rcond=None)
    resid = change - x @ beta
    att = float(resid[treated].mean())

    n = change.size
    p_treated = treated.mean()
    gram = x_control.T @ x_control / n
    leverage = np.linalg.solve(gram, x[treated].sum(axis=0) / (n * p_treated))
    psi = treated * (resid - att) / p_treated - control * resid * (x @ leverage)
    return att, psi


def _base_index(group_index: int, time_index: int, base_period: BasePeriod) -> int | None:
    """Index of the comparison year, or None when the cell cannot be estimated."""
    if base_period == "universal" or time_index >= group_index:
        return None if time_index == group_index - 1 else group_index - 1
    return time_index - 1 if time_index > 0 else None


def _control_mask(
    cohort: np.ndarray, group: int, last_year_used: int, kind: ControlGroup
) -> np.ndarray:
    """Comparison units must be untreated in both years of the difference."""
    never = cohort == 0
    if kind == "never":
        return never
    return never | ((cohort > last_year_used) & (cohort != group))


def estimate_group_time(
    panel: Panel,
    control: ControlGroup = "never",
    base_period: BasePeriod = "varying",
) -> GroupTimeResult:
    """Estimate ATT(g, t) for every cohort and every usable year."""
    n = panel.n_units
    constant = np.ones((n, 1))
    x = constant if panel.covariates is None else np.hstack([constant, panel.covariates])

    rows: list[dict[str, float | int | bool]] = []
    columns: list[np.ndarray] = []
    for group in panel.groups:
        group_index = int(np.searchsorted(panel.years, group))
        if group_index == 0:
            raise ValueError("units treated in the first year have no base period")
        treated = panel.cohort == group
        for time_index in range(panel.years.size):
            year = int(panel.years[time_index])
            base = _base_index(group_index, time_index, base_period)
            if base is None:
                continue
            last_year_used = int(panel.years[max(base, time_index)])
            mask = _control_mask(panel.cohort, int(group), last_year_used, control)
            if not mask.any():
                continue
            change = panel.y[:, time_index] - panel.y[:, base]
            att, psi = outcome_regression_did(change, treated, mask, x)
            rows.append({
                "group": int(group),
                "time": year,
                "att": att,
                "post": year >= group,
                "n_treated": int(treated.sum()),
                "n_control": int(mask.sum()),
            })
            columns.append(psi)
    return GroupTimeResult(pd.DataFrame(rows), np.column_stack(columns), panel)
