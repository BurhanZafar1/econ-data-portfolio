"""Goodman-Bacon (2021) decomposition of the TWFE coefficient.

Theorem 1 of the paper writes the TWFE estimate as a weighted average of every
two group, two period comparison in a balanced panel. Weights sum to one and
come from group sizes and from the variance of treatment inside each pair.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from staggered_did.panel import Panel

EARLY_VS_LATE = "Earlier vs later treated"
LATE_VS_EARLY = "Later vs earlier treated"
TREATED_VS_UNTREATED = "Treated vs untreated"


def _window_change(
    means: np.ndarray, before: np.ndarray, after: np.ndarray
) -> float:
    """Change in a group's mean outcome between two sets of years."""
    return float(means[after].mean() - means[before].mean())


def decompose(panel: Panel) -> pd.DataFrame:
    """Return every 2x2 comparison with its estimate and normalized weight.

    Units treated in the first year never switch inside the panel, so they
    join the always untreated units as a fixed comparison group.
    """
    first_year = panel.years[0]
    in_window = panel.cohort > first_year
    timing = np.where(in_window, panel.cohort, 0)
    switchers = np.unique(timing[timing > 0])

    share = {g: float(np.mean(timing == g)) for g in switchers}
    treated_share = {
        g: float(np.mean(panel.years >= g)) for g in switchers
    }
    means = {g: panel.y[timing == g].mean(axis=0) for g in switchers}

    rows: list[dict[str, object]] = []
    n_untreated = float(np.mean(timing == 0))
    if n_untreated > 0:
        untreated_means = panel.y[timing == 0].mean(axis=0)
        for g in switchers:
            post = panel.years >= g
            estimate = _window_change(means[g], ~post, post) - _window_change(
                untreated_means, ~post, post
            )
            pair = share[g] + n_untreated
            mix = share[g] / pair
            d_bar = treated_share[g]
            rows.append({
                "treated": int(g),
                "control": "Untreated",
                "type": TREATED_VS_UNTREATED,
                "estimate": estimate,
                "raw_weight": pair**2 * mix * (1 - mix) * d_bar * (1 - d_bar),
            })

    for i, early in enumerate(switchers):
        for late in switchers[i + 1:]:
            pre = panel.years < early
            mid = (panel.years >= early) & (panel.years < late)
            post = panel.years >= late
            pair = share[early] + share[late]
            mix = share[early] / pair
            d_early, d_late = treated_share[early], treated_share[late]
            gap = d_early - d_late
            early_estimate = _window_change(means[early], pre, mid) - _window_change(
                means[late], pre, mid
            )
            late_estimate = _window_change(means[late], mid, post) - _window_change(
                means[early], mid, post
            )
            rows.append({
                "treated": int(early),
                "control": str(late),
                "type": EARLY_VS_LATE,
                "estimate": early_estimate,
                "raw_weight": (pair * (1 - d_late)) ** 2 * mix * (1 - mix)
                * (gap / (1 - d_late)) * ((1 - d_early) / (1 - d_late)),
            })
            rows.append({
                "treated": int(late),
                "control": str(early),
                "type": LATE_VS_EARLY,
                "estimate": late_estimate,
                "raw_weight": (pair * d_early) ** 2 * mix * (1 - mix)
                * (d_late / d_early) * (gap / d_early),
            })

    table = pd.DataFrame(rows)
    raw_weight = table.pop("raw_weight")
    table["weight"] = raw_weight / raw_weight.sum()
    return table.sort_values("weight", ascending=False, ignore_index=True)


def cohort_weighted_long_difference(table: pd.DataFrame, panel: Panel) -> float:
    """Treated vs untreated comparisons, averaged with cohort size weights.

    Each comparison uses every pre treatment year as its base, while a
    group time effect uses only the last one. The gap between this number and
    the overall group effect measures sensitivity to that base period choice.
    """
    rows = table[table["type"] == TREATED_VS_UNTREATED]
    sizes = rows["treated"].map(lambda g: int(np.sum(panel.cohort == g))).to_numpy()
    return float(np.average(rows["estimate"].to_numpy(), weights=sizes))


def summarize(table: pd.DataFrame) -> pd.DataFrame:
    """Total weight and weighted average estimate by comparison type."""
    grouped = table.groupby("type", sort=True)
    out = grouped["weight"].sum().to_frame("weight")
    weighted = table.assign(product=table["weight"] * table["estimate"])
    out["avg_estimate"] = weighted.groupby("type")["product"].sum() / out["weight"]
    return out.reset_index()
