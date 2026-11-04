"""Standard errors, joint bands and the parallel trends pre test."""

from __future__ import annotations

import numpy as np
from scipy import stats


def _cluster_sums(influence: np.ndarray, clusters: np.ndarray) -> np.ndarray:
    """Sum influence functions within each cluster, returning G by K."""
    labels, index = np.unique(clusters, return_inverse=True)
    totals = np.zeros((labels.size, influence.shape[1]))
    np.add.at(totals, index, influence)
    return totals


def covariance(
    influence: np.ndarray, clusters: np.ndarray | None = None
) -> np.ndarray:
    """Covariance of the estimates from their influence functions.

    Without clusters this treats units as independent, as the did package does
    by default. With clusters it applies the G / (G - 1) small sample factor.
    """
    n = influence.shape[0]
    if clusters is None:
        return influence.T @ influence / n**2
    totals = _cluster_sums(influence, clusters)
    g = totals.shape[0]
    return (g / (g - 1)) * totals.T @ totals / n**2


def standard_errors(
    influence: np.ndarray, clusters: np.ndarray | None = None
) -> np.ndarray:
    """Standard error of each column of the influence matrix."""
    return np.sqrt(np.diag(covariance(influence, clusters)))


def sup_t_critical_value(
    influence: np.ndarray,
    clusters: np.ndarray,
    seed: int,
    draws: int = 2000,
    level: float = 0.95,
) -> float:
    """Critical value for a joint band, by a cluster multiplier bootstrap.

    Each draw flips the sign of every cluster's total with a Rademacher weight
    and records the largest studentized deviation across all parameters.
    """
    rng = np.random.default_rng(seed)
    totals = _cluster_sums(influence, clusters)
    n = influence.shape[0]
    se = standard_errors(influence, clusters)
    g = totals.shape[0]
    signs = rng.choice([-1.0, 1.0], size=(draws, g))
    deviations = np.sqrt(g / (g - 1)) * signs @ totals / n
    return float(np.quantile(np.abs(deviations / se).max(axis=1), level))


def wald_pretest(
    estimates: np.ndarray, influence: np.ndarray, clusters: np.ndarray | None = None
) -> tuple[float, int, float]:
    """Joint test that pre treatment ATT cells are all zero."""
    cov = covariance(influence, clusters)
    statistic = float(estimates @ np.linalg.solve(cov, estimates))
    df = estimates.size
    return statistic, df, float(stats.chi2.sf(statistic, df))
