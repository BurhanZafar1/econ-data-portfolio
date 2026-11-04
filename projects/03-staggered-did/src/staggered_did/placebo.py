"""Design based checks for a policy set by a small number of states.

Cluster robust formulas lean on many treated clusters and fail with one. In
the spirit of Conley and Taber (2011), these checks compare an estimate with
what the same calculation gives when treatment is assigned where it did not
happen.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from staggered_did.aggregate import group_att
from staggered_did.group_time import estimate_group_time
from staggered_did.inference import standard_errors
from staggered_did.panel import Panel, drop_cluster


def _mean_change_gap(
    change: np.ndarray, treated: np.ndarray, control: np.ndarray
) -> float:
    return float(change[treated].mean() - change[control].mean())


def state_placebo_test(panel: Panel, group: int, state: int) -> pd.DataFrame:
    """Actual and placebo post treatment effects with rank based p values.

    Placebo states are the never treated states. Each one takes a turn as the
    pretend treated state, compared with the other never treated states. The
    final row averages the effects over all post treatment years.
    """
    base = int(np.searchsorted(panel.years, group)) - 1
    never = panel.cohort == 0
    in_state = panel.clusters == state
    post_years = panel.years[panel.years >= group]
    placebo_states = np.unique(panel.clusters[never])

    changes = {
        int(year): panel.y[:, list(panel.years).index(year)] - panel.y[:, base]
        for year in post_years
    }
    changes_mean = np.mean(list(changes.values()), axis=0)
    labelled: list[tuple[int | str, np.ndarray]] = [*changes.items(), ("average", changes_mean)]

    rows = []
    for label, change in labelled:
        actual = _mean_change_gap(change, in_state, never)
        placebos = np.array([
            _mean_change_gap(
                change,
                panel.clusters == s,
                never & (panel.clusters != s),
            )
            for s in placebo_states
        ])
        extreme = int(np.sum(np.abs(placebos) >= abs(actual)))
        rows.append({
            "year": label,
            "actual": actual,
            "placebo_q05": float(np.quantile(placebos, 0.05)),
            "placebo_q95": float(np.quantile(placebos, 0.95)),
            "n_placebos": placebos.size,
            "n_as_extreme": extreme,
            "p_value": (1 + extreme) / (1 + placebos.size),
        })
    return pd.DataFrame(rows)


def _overall_with_t(panel: Panel) -> tuple[float, float]:
    """Overall group effect and its state clustered t statistic."""
    result = group_att(estimate_group_time(panel))
    estimate = float(result.estimate[-1])
    se = float(standard_errors(result.influence, panel.clusters)[-1])
    return estimate, estimate / se


def randomization_test(panel: Panel, draws: int, seed: int) -> pd.DataFrame:
    """Shuffle treatment cohorts across states and recompute the overall effect.

    Whole states swap cohorts, so assignment stays at the state level. Both the
    raw estimate and its t statistic are tested, because states differ in size.
    """
    rng = np.random.default_rng(seed)
    states, index = np.unique(panel.clusters, return_inverse=True)
    state_cohort = np.array([panel.cohort[panel.clusters == s][0] for s in states])
    actual, actual_t = _overall_with_t(panel)

    estimates, t_stats = np.empty(draws), np.empty(draws)
    for draw in range(draws):
        shuffled = rng.permutation(state_cohort)[index]
        estimates[draw], t_stats[draw] = _overall_with_t(replace(panel, cohort=shuffled))
    return pd.DataFrame([{
        "draws": draws,
        "estimate": actual,
        "t_statistic": actual_t,
        "sd_under_shuffling": float(estimates.std(ddof=1)),
        "p_value_estimate": (1 + np.sum(np.abs(estimates) >= abs(actual))) / (1 + draws),
        "p_value_t": (1 + np.sum(np.abs(t_stats) >= abs(actual_t))) / (1 + draws),
    }])


def leave_one_state_out(panel: Panel) -> pd.DataFrame:
    """Overall effect after dropping each treated state in turn."""
    treated_states = np.unique(panel.clusters[panel.cohort > 0])
    rows = []
    for state in treated_states:
        estimate, _ = _overall_with_t(drop_cluster(panel, state))
        rows.append({"dropped_state_fips": int(state), "estimate": estimate})
    return pd.DataFrame(rows)
