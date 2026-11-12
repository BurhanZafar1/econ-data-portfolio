"""Regression models for the cartel overcharge.

Two standard ways to build the "but for" price (European Commission 2013,
Practical Guide, Part 2, Section II on comparator based methods):

1. Dummy variable method. Regress log price on a cartel indicator and
   controls over all weeks. The cartel coefficient b is the average log
   overcharge, so the but for price of a cartel week is P * exp(-b).
2. Forecasting method. Fit the price model on non cartel weeks only, then
   predict the price each cartel week would have had without the cartel.

Weekly prices are autocorrelated, so standard errors are Newey-West HAC.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm

from overcharge.data import N_SEASONS, season_dummies

# Newey-West (1994) plug-in rule, floor(4 * (T/100)^(2/9)), gives 5 for T = 328.
HAC_LAGS = 5


@dataclass(frozen=True)
class DummyEstimate:
    """Cartel coefficient from one dummy variable regression."""

    name: str
    b: float
    se: float
    n: int

    @property
    def overcharge_pct(self) -> float:
        """Kennedy (1981) corrected percent effect of the dummy, exp(b - var/2) - 1."""
        return float(np.exp(self.b - 0.5 * self.se**2) - 1)

    def ci(self, z: float = 1.96) -> tuple[float, float]:
        """Confidence interval for b."""
        return self.b - z * self.se, self.b + z * self.se


def design(df: pd.DataFrame, seasons: bool, lakes: bool, trend: bool) -> pd.DataFrame:
    """Control variables (with a constant) for the log price equation."""
    parts = []
    if seasons:
        parts.append(season_dummies(df))
    if lakes:
        parts.append(df[["lakes"]].astype(float))
    if trend:
        parts.append((df["week"] / 52.0).rename("trend_years"))
    controls = pd.concat(parts, axis=1) if parts else pd.DataFrame(index=df.index)
    return sm.add_constant(controls, has_constant="add")


def fit_dummy(
    df: pd.DataFrame,
    name: str,
    seasons: bool = True,
    lakes: bool = True,
    trend: bool = False,
    hac_lags: int = HAC_LAGS,
) -> DummyEstimate:
    """OLS of log price on the cartel dummy and controls, HAC standard errors."""
    X = pd.concat([df[["cartel"]].astype(float), design(df, seasons, lakes, trend)], axis=1)
    fit = sm.OLS(df["log_price"], X).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    return DummyEstimate(name, float(fit.params["cartel"]), float(fit.bse["cartel"]), len(df))


def drop_transition_weeks(df: pd.DataFrame, weeks: int = 2) -> pd.DataFrame:
    """Remove the first `weeks` weeks of every regime spell except the first.

    Prices may adjust with a lag when collusion starts or breaks down, so
    those weeks are a mix of both regimes.
    """
    position_in_spell = df.groupby("episode").cumcount()
    keep = (df["episode"] == 0) | (position_in_spell >= weeks)
    return df.loc[keep].reset_index(drop=True)


@dataclass(frozen=True)
class Forecast:
    """But for prices from the forecasting method."""

    but_for_price: pd.Series  # dollars per 100 lbs, indexed like the input
    smearing: float


def forecast_design(df: pd.DataFrame, trend: bool) -> pd.DataFrame:
    """All 13 season indicators (no constant), lakes, and optionally a trend."""
    seasons = pd.Categorical(df["season"], categories=range(1, N_SEASONS + 1))
    parts = [
        pd.get_dummies(seasons, prefix="seas").astype(float).set_axis(df.index),
        df[["lakes"]].astype(float),
    ]
    if trend:
        parts.append((df["week"] / 52.0).rename("trend_years"))
    return pd.concat(parts, axis=1)


def fit_forecast(train: pd.DataFrame, target: pd.DataFrame, trend: bool = False) -> Forecast:
    """Fit log price on seasons and lakes using `train`, predict `target` prices.

    Every target season must appear in the training weeks, otherwise its
    level is not identified. Retransformation from logs uses a smearing factor,
    the mean of exp(residual) in the training data (Duan 1983).
    """
    unseen = set(target["season"]) - set(train["season"])
    if unseen:
        raise ValueError(f"seasons {sorted(unseen)} are not in the training weeks")
    X_train = forecast_design(train, trend)
    X_train = X_train.loc[:, X_train.any()]  # drop seasons absent from training
    fit = sm.OLS(train["log_price"], X_train).fit()
    smearing = float(np.mean(np.exp(fit.resid)))
    X_target = forecast_design(target, trend)[X_train.columns]
    predicted = np.exp(X_target.to_numpy() @ fit.params.to_numpy()) * smearing
    return Forecast(pd.Series(predicted, index=target.index), smearing)


def leave_one_episode_out(df: pd.DataFrame, trend: bool = False) -> pd.DataFrame:
    """Validate the forecasting model on price war weeks it never saw.

    For each price war episode, fit on the other war weeks and predict the
    held out episode. Held out weeks in a season that no other war week
    covers cannot be predicted and are skipped (counted in `weeks_skipped`).
    Returns one row per episode with the mean percent error of the
    predicted price against the actual price war price.
    """
    war = df[df["cartel"] == 0]
    rows = []
    for episode, held_out in war.groupby("episode"):
        train = war[war["episode"] != episode]
        scorable = held_out[held_out["season"].isin(set(train["season"]))]
        predicted = fit_forecast(train, scorable, trend).but_for_price
        rows.append(
            {
                "episode": int(episode),
                "first_week": int(held_out["week"].min()),
                "weeks_scored": len(scorable),
                "weeks_skipped": len(held_out) - len(scorable),
                "mean_pct_error": float((predicted / scorable["price"] - 1).mean()),
            }
        )
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class PermutationResult:
    """Outcome of the circular shift placebo test."""

    n_placebos: int
    n_as_large: int

    @property
    def p_value(self) -> float:
        """Share of placebos at least as large, counting the real assignment as one draw."""
        return (self.n_as_large + 1) / (self.n_placebos + 1)


def circular_shift_test(df: pd.DataFrame, observed_b: float, min_shift: int = 26) -> PermutationResult:
    """Placebo test that keeps the time structure of the regimes.

    The cartel series is rotated by every shift of at least `min_shift` weeks
    (half a year) in either direction, so each placebo has the same number and
    length of price wars, just at the wrong dates. Counts how many placebo
    coefficients are at least as large in absolute value as the real one.
    """
    X_controls = design(df, seasons=True, lakes=True, trend=False).to_numpy()
    y = df["log_price"].to_numpy()
    n = len(df)
    placebo = []
    for shift in range(min_shift, n - min_shift + 1):
        d = np.roll(df["cartel"].to_numpy(), shift).astype(float)
        coef, *_ = np.linalg.lstsq(np.column_stack([d, X_controls]), y, rcond=None)
        placebo.append(coef[0])
    as_large = int(np.sum(np.abs(np.array(placebo)) >= abs(observed_b)))
    return PermutationResult(len(placebo), as_large)


def two_stage_least_squares(
    y: np.ndarray, X: np.ndarray, Z: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """2SLS coefficients with heteroskedasticity robust (HC1) standard errors.

    X holds all regressors (endogenous and exogenous), Z all instruments
    (excluded instruments plus the exogenous regressors).
    """
    Pz_X = Z @ np.linalg.lstsq(Z, X, rcond=None)[0]  # first stage fitted values
    bread = np.linalg.inv(Pz_X.T @ Pz_X)
    beta = bread @ Pz_X.T @ y
    resid = y - X @ beta  # structural residuals use the actual regressors
    meat = (Pz_X * resid[:, None] ** 2).T @ Pz_X
    n, k = X.shape
    se = np.sqrt(np.diag(bread @ meat @ bread) * n / (n - k))  # HC1 small sample factor
    return beta, se


def demand_elasticity(df: pd.DataFrame) -> tuple[float, float]:
    """Price elasticity of grain shipping demand, instrumenting price with the cartel dummy.

    log Q = a + e log P + lakes + seasons; the cartel regime shifts supply,
    not demand, so it is a valid instrument for price (Porter 1983).
    """
    exog = pd.concat([df[["lakes"]].astype(float), season_dummies(df)], axis=1)
    exog = sm.add_constant(exog, has_constant="add").to_numpy()
    X = np.column_stack([df["log_price"].to_numpy(), exog])
    Z = np.column_stack([df["cartel"].to_numpy(float), exog])
    beta, se = two_stage_least_squares(df["log_quantity"].to_numpy(), X, Z)
    return float(beta[0]), float(se[0])
