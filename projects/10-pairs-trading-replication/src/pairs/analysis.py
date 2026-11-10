"""Summaries used by run.py: return statistics, costs, placebo pairs, factor regressions."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import optimize

from . import formation, portfolio, stats


def summarize(x: pd.Series, rng: np.random.Generator, n_boot: int = 2000) -> dict:
    v = x.to_numpy()
    boot = stats.stationary_bootstrap_means(v, mean_block=6.0, n_boot=n_boot, rng=rng)
    se = stats.newey_west_se(v, lags=6)
    return {
        "months": len(v),
        "mean": float(v.mean()),
        "nw_t": float(v.mean() / se),
        "ci_low": float(np.quantile(boot, 0.025)),
        "ci_high": float(np.quantile(boot, 0.975)),
        "sharpe_annual": float(stats.sharpe(v) * np.sqrt(12)),
        "share_negative": float((v < 0).mean()),
    }


def break_even_cost(returns: pd.DataFrame, first: str, last: str, cfg: portfolio.Config) -> float:
    """Cost per leg per side (fraction of notional) at which the committed mean is zero.

    NaN when the gross mean is already negative (no break even cost exists)."""

    def mean_at(c: float) -> float:
        return portfolio.run(returns, first, last, replace(cfg, cost=c)).monthly["committed"].mean()

    if mean_at(0.0) <= 0:
        return float("nan")
    return float(optimize.brentq(mean_at, 0.0, 0.02, xtol=1e-6))


def placebo_means(returns: pd.DataFrame, first: str, last: str, cfg: portfolio.Config,
                  draws: int, seed: int) -> np.ndarray:
    """Committed mean of the same rule on randomly drawn pairs (no distance information)."""
    rng = np.random.default_rng(seed)
    out = np.empty(draws)
    for d in range(draws):
        sel = lambda r, rng=rng: formation.random_pairs(r.shape[1], cfg.top, rng, r)  # noqa: E731
        out[d] = portfolio.run(returns, first, last, replace(cfg, selector=sel)).monthly["committed"].mean()
    return out


def factor_regression(x: pd.Series, factors: pd.DataFrame) -> pd.DataFrame:
    """OLS of monthly pairs returns on Fama-French 3, momentum and short term reversal (NW 6 lags)."""
    cols = ["Mkt-RF", "SMB", "HML", "Mom", "ST_Rev"]
    df = pd.concat([x.rename("y"), factors[cols]], axis=1, join="inner").dropna()
    fit = sm.OLS(df["y"], sm.add_constant(df[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    return pd.DataFrame({"coef": fit.params, "t": fit.tvalues}).assign(r2=fit.rsquared, n=int(fit.nobs))
