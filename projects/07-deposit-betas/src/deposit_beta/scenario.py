"""Project deposit rates and deposit interest cost under funds rate scenarios.

The projection feeds a funds rate path through the estimated lag coefficients:

    deposit[t] = deposit[t-1] + sum_k up[k] * d_ff_plus[t-k] + sum_k down[k] * d_ff_minus[t-k]

The intercept is left out on purpose: it measures average drift unrelated to policy
moves, is statistically zero in the main sample, and would otherwise add a trend to
every scenario. Rates are floored at zero.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .regression import PassThrough


@dataclass(frozen=True)
class Scenario:
    """Funds rate changes (percentage points) applied in given future months."""

    name: str
    moves: dict[int, float]  # month number (1 = first projected month) -> change

    def path(self, horizon: int) -> np.ndarray:
        """Monthly funds rate changes for months 1..horizon."""
        changes = np.zeros(horizon)
        for month, move in self.moves.items():
            if not 1 <= month <= horizon:
                raise ValueError(f"{self.name}: month {month} outside horizon")
            changes[month - 1] = move
        return changes


# Quarter point steps, roughly one every three months, as the FOMC moved in 2024-2025.
SCENARIOS: tuple[Scenario, ...] = (
    Scenario("Hold", {}),
    Scenario("Cut 100bp", {2: -0.25, 5: -0.25, 8: -0.25, 11: -0.25}),
    Scenario("Hike 50bp", {2: 0.25, 5: 0.25}),
)

# Illustrative mix of interest bearing deposits; an assumption, not any real bank.
ILLUSTRATIVE_MIX: dict[str, float] = {"checking": 0.30, "savings": 0.25, "money_market": 0.25, "cd_12m": 0.20}


def project_rate(start_level: float, d_ff_history: np.ndarray, d_ff_future: np.ndarray, fit: PassThrough) -> np.ndarray:
    """Deposit rate path for each future month.

    ``d_ff_history`` holds the most recent observed funds rate changes (oldest first,
    at least ``max_lag`` of them) so moves that already happened keep passing through.
    """
    k = fit.max_lag
    if len(d_ff_history) < k:
        raise ValueError("need at least max_lag months of funds rate history")
    up, down = np.array(fit.up_lags), np.array(fit.down_lags)
    full = np.r_[d_ff_history[-k:] if k else np.array([]), d_ff_future]
    level, path = start_level, []
    for t in range(k, len(full)):
        recent = full[t - k : t + 1][::-1]  # lag 0 first
        level = max(level + up @ np.clip(recent, 0, None) + down @ np.clip(recent, None, 0), 0.0)
        path.append(level)
    return np.array(path)


def run_scenarios(
    changes: pd.DataFrame,
    fits: dict[str, PassThrough],
    scenarios: tuple[Scenario, ...] = SCENARIOS,
    mix: dict[str, float] = ILLUSTRATIVE_MIX,
    horizon: int = 12,
) -> pd.DataFrame:
    """Projected rates and annualized interest cost per $1 billion of deposits."""
    if abs(sum(mix.values()) - 1) > 1e-9:
        raise ValueError("deposit mix must sum to one")
    last = changes.iloc[-1]
    history = changes["d_fedfunds"].to_numpy()
    rows = []
    for scenario in scenarios:
        future = scenario.path(horizon)
        ff_path = last["fedfunds"] + np.cumsum(future)
        rates = {p: project_rate(last[p], history, future, fits[p]) for p in mix}
        for month in range(horizon):
            row = {"scenario": scenario.name, "month": month + 1, "fedfunds": ff_path[month]}
            row.update({p: rates[p][month] for p in mix})
            blended = sum(mix[p] * rates[p][month] for p in mix)
            row["blended_rate"] = blended
            row["cost_per_bn_musd"] = blended / 100 * 1_000  # percent of $1bn, in $ millions
            rows.append(row)
    return pd.DataFrame(rows)
