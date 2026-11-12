"""Predictive panel regressions (Fig. 1), factor regressions (Tables 2 and 3) and summaries."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import stats


def pooled_lag_tstats(monthly: pd.DataFrame, vol: pd.DataFrame, lags: range, sign: bool = False,
                      first: str | None = None, last: str | None = None) -> pd.DataFrame:
    """Paper eqs. (2) and (3): pooled regression of r_t / sigma_{t-1} on the lag h signal.

    The dependent month t runs from `first` to `last`; lagged regressors may come from
    earlier months. Standard errors are clustered by month. Returns slope and t per lag.
    """
    scaled = monthly / vol.shift(1)  # r_t / sigma_{t-1}
    y = scaled.loc[pd.Period(first, "M") if first else None: pd.Period(last, "M") if last else None]
    rows = []
    for h in lags:
        x = (np.sign(monthly.shift(h)) if sign else scaled.shift(h)).reindex(y.index)
        stacked = pd.DataFrame({"y": y.stack(), "x": x.stack()}).dropna()
        months = stacked.index.get_level_values(0).astype(str).to_numpy()
        fit = stats.ols(stacked["y"].to_numpy(), stacked["x"].to_numpy(), ["x"], cov="cluster", groups=months)
        rows.append({"lag": h, "beta": fit.coef[1], "t": fit.t[1], "nobs": fit.nobs})
    return pd.DataFrame(rows).set_index("lag")


def to_quarterly(frame: pd.DataFrame) -> pd.DataFrame:
    """Compound monthly returns into calendar quarters; keep complete quarters only."""
    grouped = (1.0 + frame).groupby(frame.index.asfreq("Q"))
    out = grouped.prod() - 1.0
    return out[grouped.size() == 3]


def factor_regression(y: pd.Series, factors: pd.DataFrame, cols: list[str], quarterly: bool = False,
                      lags: int = 0) -> stats.OLS:
    """Time series regression of y on factors; quarterly uses non-overlapping compounded quarters."""
    frame = pd.concat([y.rename("y"), factors[cols]], axis=1, join="inner").dropna()
    if quarterly:
        frame = to_quarterly(frame)
    cov = "nw" if lags else "nonrobust"
    return stats.ols(frame["y"].to_numpy(), frame[cols].to_numpy(), cols, cov=cov, lags=lags)


def straddle_regression(y: pd.Series, market: pd.Series) -> stats.OLS:
    """Table 3 Panel C first row: quarterly TSMOM on the market return and its square."""
    frame = pd.concat([y.rename("y"), market.rename("m")], axis=1, join="inner").dropna()
    q = to_quarterly(frame)
    x = np.column_stack([q["m"], q["m"] ** 2])
    return stats.ols(q["y"].to_numpy(), x, ["MKT", "MKT2"], cov="nonrobust")


def summarize(x: pd.Series, rng: np.random.Generator, n_boot: int = 2000, block: int = 12) -> dict:
    """Annualized mean, volatility, Sharpe with a moving block bootstrap 95% interval, NW t of the mean."""
    v = x.dropna().to_numpy()
    boot = stats.block_bootstrap_sharpe(v, block, n_boot, rng)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {
        "first": str(x.dropna().index[0]),
        "last": str(x.dropna().index[-1]),
        "months": len(v),
        "mean_ann": 12 * v.mean(),
        "vol_ann": np.sqrt(12) * v.std(ddof=1),
        "sharpe": stats.sharpe(v),
        "sharpe_lo": lo,
        "sharpe_hi": hi,
        "t_nw": v.mean() / stats.newey_west_se(v, 12),
        "skew": float(pd.Series(v).skew()),
        "max_drawdown": float((np.cumprod(1 + v) / np.maximum.accumulate(np.cumprod(1 + v)) - 1).min()),
    }
