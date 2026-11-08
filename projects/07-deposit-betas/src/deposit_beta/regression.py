"""Asymmetric distributed lag regression of deposit rate changes on funds rate changes.

    d_deposit[t] = a + sum_k up[k] * d_ff_plus[t-k] + sum_k down[k] * d_ff_minus[t-k] + e[t]

where d_ff_plus = max(d_ff, 0) and d_ff_minus = min(d_ff, 0). The long run (cumulative)
beta for rising rates is sum_k up[k], and for falling rates sum_k down[k]. Standard
errors are Newey and West (1987) heteroskedasticity and autocorrelation consistent.
OLS and the covariance matrix are written out in numpy so every step is visible; a
test checks them against statsmodels.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class OLSResult:
    """Coefficients, HAC covariance and fit statistics for one regression."""

    names: tuple[str, ...]
    params: np.ndarray
    cov: np.ndarray
    nobs: int
    r_squared: float
    hac_lags: int

    def combination(self, weights: np.ndarray) -> tuple[float, float]:
        """Estimate and standard error of the linear combination weights @ params."""
        value = float(weights @ self.params)
        se = float(np.sqrt(weights @ self.cov @ weights))
        return value, se


def newey_west_lags(nobs: int) -> int:
    """Rule of thumb bandwidth floor(4 * (T / 100) ** (2 / 9)) from Newey and West (1994)."""
    return int(np.floor(4 * (nobs / 100) ** (2 / 9)))


def ols_hac(y: np.ndarray, x: np.ndarray, names: tuple[str, ...], lags: int | None = None) -> OLSResult:
    """OLS with a Bartlett kernel HAC covariance and the n / (n - k) small sample factor.

    ``x`` must already include a constant column if one is wanted.
    """
    n, k = x.shape
    if n <= k:
        raise ValueError("more regressors than observations")
    lags = newey_west_lags(n) if lags is None else lags
    xtx_inv = np.linalg.inv(x.T @ x)
    params = xtx_inv @ x.T @ y
    resid = y - x @ params
    scores = x * resid[:, None]  # row t is x_t * e_t

    meat = scores.T @ scores
    for lag in range(1, lags + 1):
        weight = 1 - lag / (lags + 1)  # Bartlett weights keep the matrix positive semidefinite
        gamma = scores[lag:].T @ scores[:-lag]
        meat += weight * (gamma + gamma.T)
    cov = xtx_inv @ meat @ xtx_inv * n / (n - k)

    r_squared = 1 - (resid @ resid) / np.sum((y - y.mean()) ** 2)
    return OLSResult(names, params, cov, n, float(r_squared), lags)


def lag_design(d_ff: pd.Series, max_lag: int) -> pd.DataFrame:
    """Columns up_0..up_K and down_0..down_K built from the funds rate change series."""
    plus, minus = d_ff.clip(lower=0), d_ff.clip(upper=0)
    columns = {f"up_{k}": plus.shift(k) for k in range(max_lag + 1)}
    columns.update({f"down_{k}": minus.shift(k) for k in range(max_lag + 1)})
    return pd.DataFrame(columns, index=d_ff.index)


@dataclass(frozen=True)
class PassThrough:
    """Long run betas for one product and sample, plus the asymmetry test."""

    product: str
    sample: str
    max_lag: int
    nobs: int
    r_squared: float
    beta_up: float
    se_up: float
    beta_down: float
    se_down: float
    asym_diff: float
    asym_se: float
    asym_p: float
    intercept: float
    intercept_se: float
    up_lags: tuple[float, ...]
    down_lags: tuple[float, ...]


def estimate_pass_through(
    changes: pd.DataFrame, product: str, sample_mask: pd.Series, sample: str, max_lag: int
) -> PassThrough:
    """Fit the asymmetric distributed lag model for one product on one sample."""
    design = lag_design(changes["d_fedfunds"], max_lag)
    frame = design.assign(y=changes[f"d_{product}"])[sample_mask].dropna()
    regressors = list(design.columns)
    x = np.column_stack([np.ones(len(frame)), frame[regressors].to_numpy()])
    names = ("const", *regressors)
    fit = ols_hac(frame["y"].to_numpy(), x, names)

    n_lag = max_lag + 1
    up_w = np.r_[0.0, np.ones(n_lag), np.zeros(n_lag)]
    down_w = np.r_[0.0, np.zeros(n_lag), np.ones(n_lag)]
    beta_up, se_up = fit.combination(up_w)
    beta_down, se_down = fit.combination(down_w)
    diff, diff_se = fit.combination(up_w - down_w)
    dof = fit.nobs - len(fit.params)
    p_value = 2 * stats.t.sf(abs(diff / diff_se), dof)  # t reference: few observations per regressor
    return PassThrough(
        product=product,
        sample=sample,
        max_lag=max_lag,
        nobs=fit.nobs,
        r_squared=fit.r_squared,
        beta_up=beta_up,
        se_up=se_up,
        beta_down=beta_down,
        se_down=se_down,
        asym_diff=diff,
        asym_se=diff_se,
        asym_p=float(p_value),
        intercept=float(fit.params[0]),
        intercept_se=float(np.sqrt(fit.cov[0, 0])),
        up_lags=tuple(float(v) for v in fit.params[1 : 1 + n_lag]),
        down_lags=tuple(float(v) for v in fit.params[1 + n_lag :]),
    )


def pass_through_table(results: list[PassThrough]) -> pd.DataFrame:
    """Flatten results into a table (lag coefficients dropped for readability)."""
    rows = [{k: v for k, v in vars(r).items() if k not in ("up_lags", "down_lags")} for r in results]
    return pd.DataFrame(rows)
