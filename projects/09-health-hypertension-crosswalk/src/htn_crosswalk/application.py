"""Final crosswalk table and its application to BRFSS state self reports."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .brfss import plausible, time_matched_cycles, to_proportions
from .crosswalk import N_DRAWS, Spec, adjust_draws, fit_crosswalk, summarise_draws
from .extract import AGE_LABELS, XW_GROUP, XW_LABELS
from .validation import Z975


def crosswalk_table(paired: pd.DataFrame, spec: Spec) -> pd.DataFrame:
    """Crosswalk coefficients with 95% confidence intervals, plus the paired inputs they summarise.

    Prevalence, sensitivity and specificity are the means over the cycles the
    crosswalk is fitted on (equal weight per cycle, as in the fit).
    """
    crosswalk = fit_crosswalk(paired, spec)
    used = paired[paired["cycle"].isin(crosswalk.cycles)]
    by = ["xw_group", "sex"] if spec.by_sex else ["xw_group"]
    summary = used.groupby(by, sort=False)[["p_self", "p_meas", "sens", "spec", "n"]].agg(
        {"p_self": "mean", "p_meas": "mean", "sens": "mean", "spec": "mean", "n": "sum"}
    )
    coef = pd.DataFrame(
        {"d": crosswalk.model.beta, "d_se": crosswalk.model.se},
        index=list(crosswalk.model.names),
    )
    keys = [" ".join(map(str, idx)) if isinstance(idx, tuple) else idx for idx in summary.index]
    table = summary.reset_index()
    table["d"] = coef.loc[keys, "d"].to_numpy()
    table["d_lower"] = table["d"] - Z975 * coef.loc[keys, "d_se"].to_numpy()
    table["d_upper"] = table["d"] + Z975 * coef.loc[keys, "d_se"].to_numpy()
    table["tau"] = np.sqrt(crosswalk.model.tau2)
    table["cycles"] = f"{crosswalk.cycles[0]} to {crosswalk.cycles[-1]}"
    table["xw_group"] = pd.Categorical(table["xw_group"], XW_LABELS, ordered=True)
    return table.sort_values(by).reset_index(drop=True)


def adjust_brfss(
    brfss: pd.DataFrame, paired_xw: pd.DataFrame, spec: Spec, rng: np.random.Generator
) -> pd.DataFrame:
    """Measured equivalent prevalence with 95% uncertainty intervals for each state, year and age.

    Each BRFSS year uses a crosswalk fitted only on NHANES cycles that start in
    or before that year (the latest spec.window of them when a window is set).
    Rows CDC suppressed (no estimate) are dropped and counted by the caller.
    """
    data = to_proportions(brfss[plausible(brfss)])
    data["xw_group"] = data["age_group"].map(XW_GROUP)
    out = []
    for year, rows in data.groupby("year", sort=True):
        cycles = time_matched_cycles(int(year), paired_xw["cycle"].unique(), spec.window)
        crosswalk = fit_crosswalk(paired_xw[paired_xw["cycle"].isin(cycles)], spec)
        draws = adjust_draws(rows["p_self"].to_numpy(), rows["se_self"].to_numpy(), rows, crosswalk, rng, N_DRAWS)
        summary = summarise_draws(draws)
        out.append(
            pd.DataFrame(
                {
                    "year": int(year),
                    "state": rows["state"].to_numpy(),
                    "age_group": rows["age_group"].to_numpy(),
                    "self_report_pct": rows["prevalence_pct"].to_numpy(),
                    "self_report_lower_pct": rows["lower_pct"].to_numpy(),
                    "self_report_upper_pct": rows["upper_pct"].to_numpy(),
                    "adjusted_pct": 100 * summary["mean"].to_numpy(),
                    "adjusted_lower_pct": 100 * summary["lower"].to_numpy(),
                    "adjusted_upper_pct": 100 * summary["upper"].to_numpy(),
                    "nhanes_cycles": f"{cycles[0]} to {cycles[-1]}",
                }
            )
        )
    return pd.concat(out, ignore_index=True)


def national_check(adjusted: pd.DataFrame, paired_age: pd.DataFrame, year: int, cycle: str) -> pd.DataFrame:
    """Median across states (self report and adjusted) next to NHANES for the matching cycle.

    A median of states is not a population weighted national figure; it is a
    plausibility check that the adjusted state values land near the measured
    national level, not a validation.
    """
    states = adjusted[adjusted["year"] == year].groupby("age_group")[["self_report_pct", "adjusted_pct"]].median()
    nhanes = paired_age[paired_age["cycle"] == cycle].set_index("age_group")[["p_self", "p_meas"]] * 100
    table = states.join(nhanes.rename(columns={"p_self": "nhanes_self_pct", "p_meas": "nhanes_measured_pct"}))
    return table.reindex(list(AGE_LABELS)).reset_index()
