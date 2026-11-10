"""Inference: Newey-West errors, stationary bootstrap, Sharpe ratios, deflated Sharpe ratio."""

from __future__ import annotations

import numpy as np
from scipy import stats as st

EULER = 0.5772156649015329


def newey_west_se(x: np.ndarray, lags: int = 6) -> float:
    """HAC standard error of the sample mean with Bartlett weights (GGR use 6 lags)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    e = x - x.mean()
    s = e @ e / n
    for lag in range(1, lags + 1):
        s += 2.0 * (1.0 - lag / (lags + 1.0)) * (e[lag:] @ e[:-lag]) / n
    return float(np.sqrt(s / n))


def stationary_bootstrap_means(
    x: np.ndarray, mean_block: float, n_boot: int, rng: np.random.Generator
) -> np.ndarray:
    """Politis and Romano (1994) stationary bootstrap distribution of the mean."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    p = 1.0 / mean_block
    out = np.empty(n_boot)
    for b in range(n_boot):
        idx = np.empty(n, dtype=int)
        idx[0] = rng.integers(n)
        new_block = rng.random(n) < p
        starts = rng.integers(n, size=n)
        for t in range(1, n):
            idx[t] = starts[t] if new_block[t] else (idx[t - 1] + 1) % n
        out[b] = x[idx].mean()
    return out


def sharpe(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    return float(x.mean() / x.std(ddof=1))


def probabilistic_sharpe(sr: float, sr_star: float, n: int, skew: float, kurt: float) -> float:
    """Bailey and Lopez de Prado PSR: P(true SR > sr_star). Non annualized SR; kurt is raw (normal = 3)."""
    denom = np.sqrt(1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2)
    return float(st.norm.cdf((sr - sr_star) * np.sqrt(n - 1.0) / denom))


def expected_max_sharpe(var_sr: float, n_trials: int) -> float:
    """Expected maximum of n_trials Sharpe ratios with zero true mean and variance var_sr."""
    z1 = st.norm.ppf(1.0 - 1.0 / n_trials)
    z2 = st.norm.ppf(1.0 - 1.0 / (n_trials * np.e))
    return float(np.sqrt(var_sr) * ((1.0 - EULER) * z1 + EULER * z2))


def deflated_sharpe(x: np.ndarray, trial_srs: np.ndarray) -> tuple[float, float]:
    """DSR of return series x given the Sharpe ratios of every trial run. Returns (DSR, SR0)."""
    x = np.asarray(x, dtype=float)
    sr0 = expected_max_sharpe(float(np.var(trial_srs, ddof=1)), len(trial_srs))
    dsr = probabilistic_sharpe(sharpe(x), sr0, len(x), float(st.skew(x)), float(st.kurtosis(x, fisher=False)))
    return dsr, sr0
