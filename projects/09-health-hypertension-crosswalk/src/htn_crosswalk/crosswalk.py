"""Fit the self report to measured crosswalk and apply it with draws.

The crosswalk predicts the logit difference d for a cell (age group, sex,
calendar time). Adjusting a self reported prevalence p is then

    p_adjusted = expit(logit(p) + d).

Uncertainty is carried by 1,000 draws that combine three sources:
  1. sampling error of the self reported input (normal on the logit scale),
  2. uncertainty in the meta-regression coefficients (multivariate normal),
  3. residual heterogeneity tau^2, because a new survey is a new "study".
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .extract import XW_LABELS
from .metareg import MetaRegression, fit_dl
from .paired import expit, logit

N_DRAWS = 1000
CENTRE_YEAR = 2010.0


@dataclass(frozen=True)
class Spec:
    """Which covariates the crosswalk uses."""

    by_sex: bool
    trend: bool
    window: int | None = None  # use only the latest `window` cycles; None uses all

    @property
    def label(self) -> str:
        cells = "age x sex" if self.by_sex else "age"
        time = " + age specific linear trend" if self.trend else ", constant over time"
        span = f", latest {self.window} cycles" if self.window else ", all cycles"
        return f"{cells} cells{time}{span}"


def cycle_mid_year(cycle_label: str) -> float:
    """Midpoint of a two year NHANES cycle (1999-2000 is centred on 1 Jan 2000).

    A single BRFSS year Y is centred on mid year, Y + 0.5; both are true midpoints.
    """
    return float(int(cycle_label[:4]) + 1)


def decades_from_centre(mid_year: np.ndarray | pd.Series) -> np.ndarray:
    """Calendar time in decades from 2010 (used only by the trend specification)."""
    return (np.asarray(mid_year, dtype=float) - CENTRE_YEAR) / 10.0


def design_matrix(cells: pd.DataFrame, spec: Spec) -> tuple[np.ndarray, tuple[str, ...]]:
    """Cell means coding: one level per crosswalk age group (and sex), plus age specific slopes in time.

    cells needs columns xw_group, mid_year and, when spec.by_sex, sex.
    """
    columns: dict[str, np.ndarray] = {}
    sexes = ("Female", "Male") if spec.by_sex else (None,)
    for age in XW_LABELS:
        is_age = (cells["xw_group"] == age).to_numpy()
        for sex in sexes:
            in_cell = is_age if sex is None else is_age & (cells["sex"] == sex).to_numpy()
            columns[age if sex is None else f"{age} {sex}"] = in_cell.astype(float)
        if spec.trend:
            columns[f"{age} trend per decade"] = is_age * decades_from_centre(cells["mid_year"])
    return np.column_stack(list(columns.values())), tuple(columns)


@dataclass(frozen=True)
class Crosswalk:
    """A fitted crosswalk model and the cycles it was fitted on."""

    spec: Spec
    model: MetaRegression
    cycles: tuple[str, ...]

    def predict(self, cells: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Mean logit difference and its predictive variance for a new survey (includes tau^2)."""
        x, _ = design_matrix(cells, self.spec)
        mean, var_beta = self.model.predict(x)
        return mean, var_beta + self.model.tau2

    def d_draws(self, cells: pd.DataFrame, rng: np.random.Generator, n_draws: int = N_DRAWS) -> np.ndarray:
        """Draws of d for each cell (cells x draws): coefficient draws plus a heterogeneity draw."""
        x, _ = design_matrix(cells, self.spec)
        beta = rng.multivariate_normal(self.model.beta, self.model.cov, size=n_draws)
        gamma = rng.normal(0.0, np.sqrt(self.model.tau2), size=(len(cells), n_draws))
        return x @ beta.T + gamma


def fit_crosswalk(paired: pd.DataFrame, spec: Spec) -> Crosswalk:
    """Fit the crosswalk on paired cycle by cell estimates (optionally the latest cycles only)."""
    if spec.window is not None:
        latest = sorted(paired["cycle"].unique())[-spec.window :]
        paired = paired[paired["cycle"].isin(latest)]
    cells = paired.assign(mid_year=paired["cycle"].map(cycle_mid_year))
    x, names = design_matrix(cells, spec)
    model = fit_dl(cells["d"].to_numpy(), cells["se_d"].to_numpy() ** 2, x, names)
    return Crosswalk(spec=spec, model=model, cycles=tuple(sorted(paired["cycle"].unique())))


def adjust_draws(
    p_self: np.ndarray,
    se_self: np.ndarray,
    cells: pd.DataFrame,
    crosswalk: Crosswalk,
    rng: np.random.Generator,
    n_draws: int = N_DRAWS,
) -> np.ndarray:
    """Draws of the measured equivalent prevalence for each self reported input (rows x draws)."""
    p_self = np.asarray(p_self, dtype=float)
    se_logit = np.asarray(se_self, dtype=float) / (p_self * (1 - p_self))
    input_draws = logit(p_self)[:, None] + rng.normal(size=(len(p_self), n_draws)) * se_logit[:, None]
    return expit(input_draws + crosswalk.d_draws(cells, rng, n_draws))


def summarise_draws(draws: np.ndarray) -> pd.DataFrame:
    """Mean and 95% uncertainty interval (2.5th and 97.5th percentiles) of each row."""
    return pd.DataFrame(
        {
            "mean": draws.mean(axis=1),
            "lower": np.percentile(draws, 2.5, axis=1),
            "upper": np.percentile(draws, 97.5, axis=1),
        }
    )


def rogan_gladen(p_obs: np.ndarray, sens: np.ndarray, spec: np.ndarray) -> np.ndarray:
    """Misclassification corrected prevalence (Rogan and Gladen 1978), clipped to 0 to 1.

    p_true = (p_obs + spec - 1) / (sens + spec - 1)
    """
    corrected = (np.asarray(p_obs) + np.asarray(spec) - 1) / (np.asarray(sens) + np.asarray(spec) - 1)
    return np.clip(corrected, 0.0, 1.0)
