"""Aggregate ATT(g, t) into summary parameters.

Follows section 3 of Callaway and Sant'Anna (2021) and the aggte routine of
the did package. Cohort size weights are themselves estimated, so their
sampling error enters the influence function (weight_influence below).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from staggered_did.group_time import GroupTimeResult


@dataclass(frozen=True)
class Aggregate:
    """Point estimates with labels and an N by K influence matrix."""

    labels: list[int | str]
    estimate: np.ndarray
    influence: np.ndarray


def weight_influence(result: GroupTimeResult, groups: np.ndarray) -> np.ndarray:
    """Influence of estimated weights p_k / sum(p), one column per entry of groups."""
    cohort = result.panel.cohort
    members = np.column_stack([cohort == g for g in groups]).astype(float)
    shares = members.mean(axis=0)
    total = shares.sum()
    deviations = members - shares
    return deviations / total - np.outer(deviations.sum(axis=1), shares) / total**2


def _weighted(
    result: GroupTimeResult, keep: np.ndarray, weights_from_size: bool = True
) -> tuple[float, np.ndarray]:
    """Combine selected ATT cells, by cohort size or equally."""
    table = result.table
    att = table["att"].to_numpy()[keep]
    psi = result.influence[:, keep]
    if not weights_from_size:
        return float(att.mean()), psi.mean(axis=1)
    groups = table["group"].to_numpy()[keep]
    shares = np.array([np.mean(result.panel.cohort == g) for g in groups])
    weights = shares / shares.sum()
    return float(weights @ att), psi @ weights + weight_influence(result, groups) @ att


def simple_att(result: GroupTimeResult) -> Aggregate:
    """Average over all post treatment cells, weighted by cohort size."""
    keep = result.table["post"].to_numpy()
    estimate, psi = _weighted(result, keep)
    return Aggregate(["simple"], np.array([estimate]), psi[:, None])


def group_att(result: GroupTimeResult) -> Aggregate:
    """Each cohort's average effect, then the size weighted overall effect."""
    table = result.table
    groups = result.panel.groups
    estimates, columns = [], []
    for g in groups:
        keep = ((table["group"] == g) & table["post"]).to_numpy()
        estimate, psi = _weighted(result, keep, weights_from_size=False)
        estimates.append(estimate)
        columns.append(psi)
    by_group = np.array(estimates)
    influence = np.column_stack(columns)

    shares = np.array([np.mean(result.panel.cohort == g) for g in groups])
    weights = shares / shares.sum()
    overall = float(weights @ by_group)
    overall_psi = influence @ weights + weight_influence(result, groups) @ by_group
    return Aggregate(
        [*(int(g) for g in groups), "overall"],
        np.append(by_group, overall),
        np.column_stack([influence, overall_psi]),
    )


def event_study(
    result: GroupTimeResult, balance_e: int | None = None
) -> Aggregate:
    """Effects by years since treatment, then the mean over post treatment years.

    With balance_e, keep only cohorts observed at least balance_e years after
    treatment and only event times up to balance_e, so that the same cohorts
    stand behind every post treatment point.
    """
    table = result.table
    event_time = (table["time"] - table["group"]).to_numpy()
    keep_cell = np.ones(event_time.size, dtype=bool)
    if balance_e is not None:
        last_year = result.panel.years[-1]
        keep_cell = (
            (last_year - table["group"].to_numpy() >= balance_e)
            & (event_time <= balance_e)
        )

    estimates, columns, labels = [], [], []
    for e in sorted(set(event_time[keep_cell].tolist())):
        keep = keep_cell & (event_time == e)
        estimate, psi = _weighted(result, keep)
        labels.append(int(e))
        estimates.append(estimate)
        columns.append(psi)

    by_event = np.array(estimates)
    influence = np.column_stack(columns)
    post = np.array(labels) >= 0
    overall = float(by_event[post].mean())
    overall_psi = influence[:, post].mean(axis=1)
    return Aggregate(
        [*labels, "overall"],
        np.append(by_event, overall),
        np.column_stack([influence, overall_psi]),
    )


def treated_states_by_event_time(result: GroupTimeResult) -> dict[int, int]:
    """Count the distinct treated states standing behind each event time."""
    table = result.table
    panel = result.panel
    counts: dict[int, int] = {}
    for e, cells in table.groupby(table["time"] - table["group"]):
        members = np.isin(panel.cohort, cells["group"].to_numpy())
        counts[int(e)] = int(np.unique(panel.clusters[members]).size)
    return counts
