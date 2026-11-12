"""Run every estimate and collect the numbers reported in the README."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from overcharge.damages import (
    damages_from_log_overcharge,
    overcharge_damages,
    volume_effect,
)
from overcharge.models import (
    DummyEstimate,
    circular_shift_test,
    demand_elasticity,
    drop_transition_weeks,
    fit_dummy,
    fit_forecast,
    leave_one_episode_out,
)

PREFERRED = "Seasons and lakes (preferred)"


@dataclass
class Results:
    """Everything run.py writes to disk."""

    table: pd.DataFrame
    preferred: DummyEstimate
    forecast_price: pd.Series
    validation: pd.DataFrame
    elasticity: tuple[float, float]
    headline: dict = field(default_factory=dict)


def specifications(df: pd.DataFrame) -> list[tuple[DummyEstimate, pd.DataFrame]]:
    """The dummy variable regression under each set of controls.

    Each estimate is paired with the sample it was fit on; damages apply b
    only to the cartel weeks of that sample.
    """
    trimmed = drop_transition_weeks(df)
    return [
        (fit_dummy(df, "No controls", seasons=False, lakes=False), df),
        (fit_dummy(df, "Seasons only", seasons=True, lakes=False), df),
        (fit_dummy(df, PREFERRED), df),
        (fit_dummy(df, "Preferred plus linear trend", trend=True), df),
        (fit_dummy(trimmed, "Preferred, transition weeks dropped"), trimmed),
        (fit_dummy(df, "Preferred, 13 HAC lags", hac_lags=13), df),
        (fit_dummy(df, "Preferred, 26 HAC lags", hac_lags=26), df),
    ]


def forecast_row(cartel_weeks: pd.DataFrame, but_for: pd.Series, label: str, n: int) -> dict:
    """Table row for a forecasting method estimate (no sampling interval)."""
    return {
        "method": f"Forecasting: {label}, fit on price war weeks",
        "weeks": n,
        "damage_weeks": len(cartel_weeks),
        "log_overcharge_b": np.nan,
        "hac_se": np.nan,
        "overcharge_pct_of_but_for": float(cartel_weeks["price"].sum() / but_for.sum() - 1),
        "damages_usd": overcharge_damages(cartel_weeks, but_for),
        "damages_low_usd": np.nan,
        "damages_high_usd": np.nan,
    }


def build_table(
    estimates: list[tuple[DummyEstimate, pd.DataFrame]], forecast_rows: list[dict]
) -> pd.DataFrame:
    """One row per method: coefficient, percent overcharge, damages and interval.

    For dummy rows the overcharge is exp(b) - 1, the same transform the
    damages use, so the percent and the dollars are consistent.
    """
    rows = []
    for est, sample in estimates:
        cartel_weeks = sample[sample["cartel"] == 1]
        low, high = est.ci()
        rows.append(
            {
                "method": "Dummy variable: " + est.name,
                "weeks": est.n,
                "damage_weeks": len(cartel_weeks),
                "log_overcharge_b": est.b,
                "hac_se": est.se,
                "overcharge_pct_of_but_for": float(np.exp(est.b) - 1),
                "damages_usd": damages_from_log_overcharge(cartel_weeks, est.b),
                "damages_low_usd": damages_from_log_overcharge(cartel_weeks, low),
                "damages_high_usd": damages_from_log_overcharge(cartel_weeks, high),
            }
        )
    rows.extend(forecast_rows)
    return pd.DataFrame(rows)


def run(df: pd.DataFrame) -> Results:
    """Estimate overcharges and damages by both methods plus robustness checks."""
    cartel_weeks = df[df["cartel"] == 1]
    war_weeks = df[df["cartel"] == 0]

    estimates = specifications(df)
    preferred = next(e for e, _ in estimates if e.name == PREFERRED)

    forecast = fit_forecast(war_weeks, cartel_weeks)
    forecast_rows = [
        forecast_row(cartel_weeks, forecast.but_for_price, "seasons and lakes", len(df)),
        forecast_row(
            cartel_weeks,
            fit_forecast(war_weeks, cartel_weeks, trend=True).but_for_price,
            "plus linear trend",
            len(df),
        ),
    ]
    table = build_table(estimates, forecast_rows)

    validation = leave_one_episode_out(df)
    elasticity = demand_elasticity(df)
    volume = volume_effect(cartel_weeks, preferred.b, elasticity[0])
    p_perm = circular_shift_test(df, preferred.b)

    preferred_row = table[table["method"].str.endswith(PREFERRED)].iloc[0]
    headline = {
        "weeks": len(df),
        "cartel_weeks": len(cartel_weeks),
        "price_war_weeks": len(war_weeks),
        "mean_price_cartel": float(cartel_weeks["price"].mean()),
        "mean_price_war": float(war_weeks["price"].mean()),
        "affected_commerce_usd": float(cartel_weeks["revenue"].sum()),
        "preferred_b": preferred.b,
        "preferred_se": preferred.se,
        "preferred_overcharge_pct": float(np.exp(preferred.b) - 1),
        "preferred_overcharge_pct_kennedy": preferred.overcharge_pct,
        "preferred_overcharge_share_of_actual": float(1 - np.exp(-preferred.b)),
        "preferred_damages_usd": float(preferred_row["damages_usd"]),
        "preferred_damages_low_usd": float(preferred_row["damages_low_usd"]),
        "preferred_damages_high_usd": float(preferred_row["damages_high_usd"]),
        "forecast_overcharge_pct": forecast_rows[0]["overcharge_pct_of_but_for"],
        "forecast_damages_usd": forecast_rows[0]["damages_usd"],
        "forecast_trend_overcharge_pct": forecast_rows[1]["overcharge_pct_of_but_for"],
        "forecast_trend_damages_usd": forecast_rows[1]["damages_usd"],
        "forecast_smearing": forecast.smearing,
        "validation_mean_abs_pct_error_weighted": float(
            np.average(validation["mean_pct_error"].abs(), weights=validation["weeks_scored"])
        ),
        "validation_mean_pct_error_weighted": float(
            np.average(validation["mean_pct_error"], weights=validation["weeks_scored"])
        ),
        "validation_episodes": len(validation),
        "validation_weeks_scored": int(validation["weeks_scored"].sum()),
        "validation_weeks_skipped": int(validation["weeks_skipped"].sum()),
        "permutation_p_value": p_perm.p_value,
        "permutation_placebos": p_perm.n_placebos,
        "permutation_placebos_as_large": p_perm.n_as_large,
        "demand_elasticity": elasticity[0],
        "demand_elasticity_se": elasticity[1],
        "lost_tons": volume.lost_tons,
        "lost_pct": volume.lost_pct,
        "deadweight_loss_usd": volume.deadweight_loss,
    }
    return Results(table, preferred, forecast.but_for_price, validation, elasticity, headline)
