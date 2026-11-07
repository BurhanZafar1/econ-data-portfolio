"""Crude and age standardized blood pressure indicators by NHANES cycle and sex."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from .standards import assign_age_group, group_label
from .survey import Design, Estimate, estimate, ratio_mean, standardized_mean

SEXES = ("Both", "Male", "Female")


@dataclass(frozen=True)
class Measure:
    """A person level indicator: column name, plain label, and unit scale for reporting."""

    name: str
    label: str
    scale: float  # 100 turns a proportion into a percent

    @property
    def is_proportion(self) -> bool:
        return self.scale == 100.0

    def interval(self, est: Estimate) -> tuple[float, float]:
        return est.ci_logit if self.is_proportion else est.ci


MEASURES: tuple[Measure, ...] = (
    Measure("htn140", "Hypertension, SBP>=140 or DBP>=90 or on medication (%)", 100.0),
    Measure("htn130", "Hypertension, SBP>=130 or DBP>=80 or on medication (%)", 100.0),
    Measure("sbp", "Mean systolic blood pressure (mmHg)", 1.0),
)


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    """Add the analysis sample flag and the binary hypertension indicators.

    Analysis sample: examined, not pregnant, at least one valid systolic and
    diastolic reading, and known medication status (the NCHS definition).
    """
    out = frame.copy()
    out["in_sample"] = (
        (out["pregnant"] == 0) & out["sbp"].notna() & out["dbp"].notna() & out["bp_med"].notna()
    )
    on_med = out["bp_med"] == 1
    out["htn140"] = ((out["sbp"] >= 140) | (out["dbp"] >= 90) | on_med).astype(float)
    out["htn130"] = ((out["sbp"] >= 130) | (out["dbp"] >= 80) | on_med).astype(float)
    return out


def _domain(cycle_frame: pd.DataFrame, sex: str, min_age: int) -> np.ndarray:
    mask = cycle_frame["in_sample"] & (cycle_frame["age"] >= min_age)
    if sex != "Both":
        mask &= cycle_frame["sex"] == sex
    return mask.to_numpy()


def estimate_cycle(
    cycle_frame: pd.DataFrame,
    measure: Measure,
    sex: str,
    groups: list[tuple[int, int]],
    std_weights: pd.Series,
) -> dict[str, Estimate]:
    """Crude and age standardized estimate of one measure for one cycle and sex.

    The design is built from every examined adult in the cycle so that all
    PSUs and strata are kept when estimating for a subpopulation.
    """
    design = Design.from_frame(cycle_frame)
    min_age = groups[0][0]
    in_domain = _domain(cycle_frame, sex, min_age)
    y = cycle_frame[measure.name].to_numpy(dtype=float)
    age_group = assign_age_group(cycle_frame["age"], groups).to_numpy()
    n = int(in_domain.sum())
    return {
        "crude": estimate(ratio_mean(y, in_domain, design), design, n),
        "age_standardized": estimate(
            standardized_mean(y, in_domain, age_group, std_weights, design), design, n
        ),
    }


def estimate_all(
    frame: pd.DataFrame,
    groups: list[tuple[int, int]],
    std_weights: pd.Series,
    measures: tuple[Measure, ...] = MEASURES,
) -> pd.DataFrame:
    """Long table: cycle x sex x measure x (crude, age standardized) with 95% intervals."""
    rows = []
    for cycle, cycle_frame in frame.groupby("cycle", sort=True):
        for measure in measures:
            for sex in SEXES:
                for kind, est in estimate_cycle(cycle_frame, measure, sex, groups, std_weights).items():
                    lo, hi = measure.interval(est)
                    rows.append(
                        {
                            "cycle": cycle,
                            "sex": sex,
                            "measure": measure.name,
                            "type": kind,
                            "estimate": est.value * measure.scale,
                            "se": est.se * measure.scale,
                            "lower95": lo * measure.scale,
                            "upper95": hi * measure.scale,
                            "df": est.df,
                            "n": est.n,
                        }
                    )
    return pd.DataFrame(rows)


def age_specific(frame: pd.DataFrame, cycle: str, groups: list[tuple[int, int]], measure: Measure) -> pd.DataFrame:
    """Design based mean of a measure by age group and sex within one cycle."""
    cycle_frame = frame[frame["cycle"] == cycle]
    design = Design.from_frame(cycle_frame)
    age_group = assign_age_group(cycle_frame["age"], groups).to_numpy()
    y = cycle_frame[measure.name].to_numpy(dtype=float)
    rows = []
    for sex in ("Male", "Female"):
        base = _domain(cycle_frame, sex, groups[0][0])
        for g in [group_label(grp) for grp in groups]:
            in_domain = base & (age_group == g)
            est = estimate(ratio_mean(y, in_domain, design), design, int(in_domain.sum()))
            lo, hi = measure.interval(est)
            rows.append(
                {
                    "sex": sex,
                    "age_group": g,
                    "estimate": est.value * measure.scale,
                    "lower95": lo * measure.scale,
                    "upper95": hi * measure.scale,
                    "n": est.n,
                }
            )
    return pd.DataFrame(rows)


def change_between(table: pd.DataFrame, first: str, last: str) -> pd.DataFrame:
    """Difference between two cycles with a 95% interval.

    NHANES cycles are independent samples, so the variance of the difference
    is the sum of the two variances. The t quantile uses the smaller of the two
    cycles' degrees of freedom, which is conservative.
    """
    keys = ["sex", "measure", "type"]
    a = table[table["cycle"] == first].set_index(keys)
    b = table[table["cycle"] == last].set_index(keys)
    diff = b["estimate"] - a["estimate"]
    se = np.sqrt(a["se"] ** 2 + b["se"] ** 2)
    t = stats.t.ppf(0.975, np.minimum(a["df"], b["df"]))
    out = pd.DataFrame({"change": diff, "se": se, "lower95": diff - t * se, "upper95": diff + t * se})
    out["from"], out["to"] = first, last
    return out.reset_index()
