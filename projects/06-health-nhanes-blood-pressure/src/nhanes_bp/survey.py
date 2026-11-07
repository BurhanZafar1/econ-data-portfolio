"""Design based estimation for stratified, clustered surveys (Taylor linearization).

Every estimator here returns a point estimate and a per person linearized
value z_i. The variance of the estimate is the with replacement variance of
the PSU totals of z within strata,

    V = sum_h n_h / (n_h - 1) * sum_j (z_hj - zbar_h)^2,

which is what SUDAAN, Stata svy and R survey compute by default for NHANES.
Confidence intervals use a t distribution with (number of PSUs minus number
of strata) degrees of freedom, as the NHANES analytic guidelines recommend;
for proportions the interval is built on the logit scale so it stays in 0-1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class Estimate:
    """A survey estimate with its design based standard error and 95% interval."""

    value: float
    se: float
    df: int
    n: int

    @property
    def ci(self) -> tuple[float, float]:
        """Symmetric t interval, used for means."""
        half = stats.t.ppf(0.975, self.df) * self.se
        return self.value - half, self.value + half

    @property
    def ci_logit(self) -> tuple[float, float]:
        """Logit transformed t interval for a proportion (always inside 0 to 1).

        The standard error is mapped to the logit scale by the delta method,
        se_logit = se / (p (1 - p)), as in R survey::svyciprop(method = "logit").
        """
        p = self.value
        if not 0.0 < p < 1.0:
            return p, p
        half = stats.t.ppf(0.975, self.df) * self.se / (p * (1.0 - p))
        centre = np.log(p / (1.0 - p))
        return float(_expit(centre - half)), float(_expit(centre + half))


def _expit(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


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

    @property
    def df(self) -> int:
        clusters = pd.DataFrame({"h": self.stratum, "j": self.psu}).drop_duplicates()
        return len(clusters) - clusters["h"].nunique()


def ratio_mean(y: np.ndarray, in_domain: np.ndarray, design: Design) -> tuple[float, np.ndarray]:
    """Weighted mean of y over a domain, and its linearized values.

    Rows outside the domain keep z = 0 but still count for their PSU, which is
    the correct subpopulation (domain) analysis.
    """
    w = design.weight * in_domain
    total_w = w.sum()
    if total_w <= 0:
        raise ValueError("Empty domain")
    y_filled = np.where(in_domain, y, 0.0)
    r = float((w * y_filled).sum() / total_w)
    z = w * (y_filled - r) / total_w
    return r, z


def standardized_mean(
    y: np.ndarray,
    in_domain: np.ndarray,
    age_group: np.ndarray,
    std_weights: pd.Series,
    design: Design,
) -> tuple[float, np.ndarray]:
    """Directly age standardized mean: sum_g s_g * mean_g, with linearized values.

    The standard weights s_g are fixed constants, so z is the s_g weighted sum
    of the group specific ratio influence values.
    """
    value = 0.0
    z = np.zeros_like(design.weight)
    for group, s_g in std_weights.items():
        r_g, z_g = ratio_mean(y, in_domain & (age_group == group), design)
        value += s_g * r_g
        z += s_g * z_g
    return value, z


def taylor_se(z: np.ndarray, design: Design) -> float:
    """Standard error from linearized values under the with replacement PSU approximation."""
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
    variance = float((n_h / (n_h - 1) * dev**2).sum())
    return float(np.sqrt(variance))


def estimate(value_and_z: tuple[float, np.ndarray], design: Design, n: int) -> Estimate:
    """Package a point estimate and its linearized values into an Estimate."""
    value, z = value_and_z
    return Estimate(value=value, se=taylor_se(z, design), df=design.df, n=n)
