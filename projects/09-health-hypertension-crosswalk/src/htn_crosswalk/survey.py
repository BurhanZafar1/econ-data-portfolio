"""Design based estimation for stratified, clustered surveys (Taylor linearization).

Each estimator returns a point estimate and per person linearized values z_i.
The variance is the with replacement variance of PSU totals of z within strata,

    V = sum_h n_h / (n_h - 1) * sum_j (z_hj - zbar_h)^2,

the default in SUDAAN, Stata svy and R survey for NHANES. Rows outside the
domain keep z = 0 but their PSU stays in the design (correct domain analysis).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Design:
    """Weights and design identifiers for the rows of one survey cycle."""

    weight: np.ndarray
    stratum: np.ndarray
    psu: np.ndarray

    @classmethod
    def from_frame(cls, frame: pd.DataFrame, weight: str = "wt_mec") -> "Design":
        return cls(
            weight=frame[weight].to_numpy(dtype=float),
            stratum=frame["stratum"].to_numpy(),
            psu=frame["psu"].to_numpy(),
        )


def ratio_mean(y: np.ndarray, in_domain: np.ndarray, design: Design) -> tuple[float, np.ndarray]:
    """Weighted mean of y over a domain, and its linearized values."""
    w = design.weight * in_domain
    total_w = w.sum()
    if total_w <= 0:
        raise ValueError("Empty domain")
    y_filled = np.where(in_domain, y, 0.0)
    r = float((w * y_filled).sum() / total_w)
    return r, w * (y_filled - r) / total_w


def taylor_variance(z: np.ndarray, design: Design) -> float:
    """Variance of a linearized statistic under the with replacement PSU approximation."""
    psu_totals = (
        pd.DataFrame({"h": design.stratum, "j": design.psu, "z": z})
        .groupby(["h", "j"], sort=True)["z"]
        .sum()
        .reset_index()
    )
    n_h = psu_totals.groupby("h")["j"].transform("size")
    if (n_h < 2).any():
        raise ValueError("Each stratum needs at least two PSUs for Taylor variance")
    dev = psu_totals["z"] - psu_totals.groupby("h")["z"].transform("mean")
    return float((n_h / (n_h - 1) * dev**2).sum())
