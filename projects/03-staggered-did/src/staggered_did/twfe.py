"""Two way fixed effects regressions with cluster robust standard errors."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from staggered_did.panel import Panel


@dataclass(frozen=True)
class Regression:
    """Coefficients with county and state clustered standard errors."""

    terms: list[int | str]
    coef: np.ndarray
    se_unit: np.ndarray
    se_cluster: np.ndarray


def two_way_demean(matrix: np.ndarray) -> np.ndarray:
    """Remove unit and year means from a balanced N by T matrix."""
    return (
        matrix
        - matrix.mean(axis=1, keepdims=True)
        - matrix.mean(axis=0, keepdims=True)
        + matrix.mean()
    )


def _clustered_se(
    x: np.ndarray, resid: np.ndarray, ids: np.ndarray, n_params: int
) -> np.ndarray:
    """CR1 sandwich. x and resid are stacked unit by year, ids label each row."""
    bread = np.linalg.inv(x.T @ x)
    labels, index = np.unique(ids, return_inverse=True)
    scores = np.zeros((labels.size, x.shape[1]))
    np.add.at(scores, index, x * resid[:, None])
    n_obs, n_clusters = x.shape[0], labels.size
    correction = (n_clusters / (n_clusters - 1)) * ((n_obs - 1) / (n_obs - n_params))
    return np.sqrt(np.diag(bread @ (scores.T @ scores) @ bread) * correction)


def fit_twfe(panel: Panel, regressors: dict[int | str, np.ndarray]) -> Regression:
    """OLS of the outcome on regressors with unit and year fixed effects."""
    y = two_way_demean(panel.y).ravel()
    x = np.column_stack([two_way_demean(r).ravel() for r in regressors.values()])
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ coef
    n_periods = panel.years.size
    unit_ids = np.repeat(np.arange(panel.n_units), n_periods)
    state_ids = np.repeat(panel.clusters, n_periods)
    # Unit effects nest in clusters, so as in standard fixed effects software
    # the small sample factor counts slopes and year effects but not unit effects.
    k = x.shape[1] + n_periods
    return Regression(
        terms=list(regressors),
        coef=coef,
        se_unit=_clustered_se(x, resid, unit_ids, k),
        se_cluster=_clustered_se(x, resid, state_ids, k),
    )


def static_twfe(panel: Panel) -> Regression:
    """The usual single coefficient on a post treatment dummy."""
    return fit_twfe(panel, {"post": panel.treated})


def event_study_twfe(panel: Panel, omit: int = -1) -> pd.DataFrame:
    """TWFE leads and lags, with event time -1 as the reference period."""
    relative = panel.years[None, :] - panel.cohort[:, None]
    ever = panel.cohort > 0
    event_times = sorted({int(e) for e in np.unique(relative[ever])} - {omit})
    dummies = {
        e: (ever[:, None] & (relative == e)).astype(float) for e in event_times
    }
    fit = fit_twfe(panel, dummies)
    return pd.DataFrame(
        {"event_time": fit.terms, "estimate": fit.coef, "se_state": fit.se_cluster}
    )
