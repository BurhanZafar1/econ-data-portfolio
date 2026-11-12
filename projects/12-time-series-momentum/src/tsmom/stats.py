"""Inference: OLS with Newey-West or clustered errors, bootstrap, Sharpe and deflated Sharpe ratios."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as st

EULER = 0.5772156649015329


@dataclass
class OLS:
    names: list[str]
    coef: np.ndarray
    se: np.ndarray
    r2: float
    nobs: int

    @property
    def t(self) -> np.ndarray:
        return self.coef / self.se

    def table(self) -> pd.DataFrame:
        return pd.DataFrame({"coef": self.coef, "se": self.se, "t": self.t}, index=self.names)


def ols(y: np.ndarray, x: np.ndarray, names: list[str], cov: str = "hc0", lags: int = 0,
        groups: np.ndarray | None = None) -> OLS:
    """OLS of y on [1, x]. cov: "nonrobust", "hc0", "nw" (Bartlett, `lags`) or "cluster" (`groups`)."""
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float).reshape(len(y), -1)
    X = np.column_stack([np.ones(len(y)), x])
    n, k = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    b = xtx_inv @ X.T @ y
    u = y - X @ b
    if cov == "nonrobust":
        v = xtx_inv * (u @ u) / (n - k)
    else:
        if cov == "hc0" or (cov == "nw" and lags == 0):
            xu = X * u[:, None]
            meat = xu.T @ xu
        elif cov == "nw":
            xu = X * u[:, None]
            meat = xu.T @ xu
            for lag in range(1, lags + 1):
                w = 1.0 - lag / (lags + 1.0)
                g = xu[lag:].T @ xu[:-lag]
                meat += w * (g + g.T)
        elif cov == "cluster":
            codes, inv = np.unique(groups, return_inverse=True)
            sums = np.zeros((len(codes), k))
            np.add.at(sums, inv, X * u[:, None])
            g = len(codes)
            meat = sums.T @ sums * (g / (g - 1.0)) * ((n - 1.0) / (n - k))
        else:
            raise ValueError(cov)
        v = xtx_inv @ meat @ xtx_inv
    r2 = 1.0 - (u @ u) / np.sum((y - y.mean()) ** 2)
    return OLS(["const", *names], b, np.sqrt(np.diag(v)), float(r2), n)


def newey_west_se(x: np.ndarray, lags: int) -> float:
    """HAC standard error of a sample mean with Bartlett weights."""
    return float(ols(np.asarray(x, dtype=float), np.empty((len(x), 0)), [], cov="nw", lags=lags).se[0])


def sharpe(x: np.ndarray, periods: int = 12) -> float:
    """Annualized Sharpe ratio of excess returns."""
    x = np.asarray(x, dtype=float)
    return float(x.mean() / x.std(ddof=1) * np.sqrt(periods))


def block_bootstrap_sharpe(x: np.ndarray, block: int, n_boot: int, rng: np.random.Generator,
                           periods: int = 12) -> np.ndarray:
    """Moving block bootstrap distribution of the annualized Sharpe ratio."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    n_blocks = int(np.ceil(n / block))
    out = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, n - block + 1, size=n_blocks)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:n]
        out[b] = sharpe(x[idx], periods)
    return out


def probabilistic_sharpe(sr: float, sr_star: float, n: int, skew: float, kurt: float) -> float:
    """Bailey and Lopez de Prado PSR, P(true SR > sr_star), per period SR; kurt is raw (normal = 3)."""
    denom = np.sqrt(1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2)
    return float(st.norm.cdf((sr - sr_star) * np.sqrt(n - 1.0) / denom))


def expected_max_sharpe(var_sr: float, n_trials: int) -> float:
    """Expected maximum of n_trials per period Sharpe ratios with zero mean and variance var_sr."""
    z1 = st.norm.ppf(1.0 - 1.0 / n_trials)
    z2 = st.norm.ppf(1.0 - 1.0 / (n_trials * np.e))
    return float(np.sqrt(var_sr) * ((1.0 - EULER) * z1 + EULER * z2))


def deflated_sharpe(x: np.ndarray, trial_srs: np.ndarray, n_trials: int | None = None) -> tuple[float, float]:
    """DSR of per period returns x given the per period Sharpe ratios of all trials. Returns (DSR, SR0)."""
    x = np.asarray(x, dtype=float)
    trial_srs = np.asarray(trial_srs, dtype=float)
    n_trials = len(trial_srs) if n_trials is None else n_trials
    sr0 = expected_max_sharpe(float(np.var(trial_srs, ddof=1)), n_trials)
    sr = float(x.mean() / x.std(ddof=1))
    dsr = probabilistic_sharpe(sr, sr0, len(x), float(st.skew(x)), float(st.kurtosis(x, fisher=False)))
    return dsr, sr0
