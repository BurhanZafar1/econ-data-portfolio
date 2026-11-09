"""Paired survey estimates of the two hypertension definitions in each NHANES cycle.

Every analysed person answers the self report question and has measured blood
pressure, so both prevalences come from the same people. The crosswalk input
is their logit difference,

    d = logit(p_measured) - logit(p_self),

and its standard error must account for the positive correlation between the
two estimates. Linearization handles this exactly: the linearized value of d is
the difference of the two linearized logits, computed person by person.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .survey import Design, ratio_mean, taylor_variance


def logit(p: np.ndarray | float) -> np.ndarray | float:
    """Log odds."""
    return np.log(p / (1.0 - p))


def expit(x: np.ndarray | float) -> np.ndarray | float:
    """Inverse of logit."""
    return 1.0 / (1.0 + np.exp(-x))


def paired_cell(cycle_frame: pd.DataFrame, in_cell: np.ndarray) -> dict[str, float]:
    """Self reported and measured prevalence, their logit difference, sensitivity and specificity.

    cycle_frame holds every examined adult of one cycle (for the design);
    in_cell flags the analysed people in the cell.
    """
    design = Design.from_frame(cycle_frame)
    self_y = cycle_frame["self_htn"].fillna(0).to_numpy(dtype=float)
    meas_y = cycle_frame["measured_htn"].fillna(0).to_numpy(dtype=float)

    p_self, z_self = ratio_mean(self_y, in_cell, design)
    p_meas, z_meas = ratio_mean(meas_y, in_cell, design)
    z_d = z_meas / (p_meas * (1 - p_meas)) - z_self / (p_self * (1 - p_self))

    # Sensitivity: share of measured hypertensives who report it.
    sens, z_sens = ratio_mean(self_y, in_cell & (meas_y == 1), design)
    # Specificity: share of measured normotensives who do not report it.
    spec, z_spec = ratio_mean(1 - self_y, in_cell & (meas_y == 0), design)

    return {
        "n": int(in_cell.sum()),
        "p_self": p_self,
        "se_self": np.sqrt(taylor_variance(z_self, design)),
        "p_meas": p_meas,
        "se_meas": np.sqrt(taylor_variance(z_meas, design)),
        "d": float(logit(p_meas) - logit(p_self)),
        "se_d": np.sqrt(taylor_variance(z_d, design)),
        "sens": sens,
        "se_sens": np.sqrt(taylor_variance(z_sens, design)),
        "spec": spec,
        "se_spec": np.sqrt(taylor_variance(z_spec, design)),
    }


def paired_estimates(extract: pd.DataFrame, by: Sequence[str]) -> pd.DataFrame:
    """One row per cycle and cell defined by the columns in `by` (for example age_group, sex)."""
    rows = []
    for cycle, cycle_frame in extract.groupby("cycle", sort=True):
        cycle_frame = cycle_frame.reset_index(drop=True)
        analysed = cycle_frame["analysis"].to_numpy() == 1
        cells = cycle_frame.loc[analysed, list(by)].drop_duplicates().sort_values(list(by))
        for cell in cells.itertuples(index=False):
            in_cell = analysed.copy()
            for col, value in zip(by, cell):
                in_cell &= cycle_frame[col].to_numpy() == value
            rows.append({"cycle": cycle, **dict(zip(by, cell)), **paired_cell(cycle_frame, in_cell)})
    return pd.DataFrame(rows)
