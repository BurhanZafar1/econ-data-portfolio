"""Rolling origin validation: predict each NHANES cycle using only the cycles before it.

For every forecast origin (a held out cycle with at least MIN_TRAIN earlier
cycles) each method is fitted on earlier cycles only, then asked to turn the
held out cycle's self reported prevalence into a measured equivalent. Nothing
from the held out cycle (its crosswalk, tau^2, sensitivity or specificity)
enters fitting.

In a held out cell the observed measured prevalence equals
expit(logit(p_self) + d_obs) exactly, so an interval for d_obs maps one to one
onto an interval for measured prevalence. That interval adds the held out
cell's own sampling variance se_d^2, because the target is itself an estimate.

Origins 2005-2006 to 2011-2012 choose among the crosswalk candidates; origins
2013-2014 to 2017-2018 then score the chosen one, so the reported error is not
the error the choice was made on.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy import stats

from .crosswalk import Spec, cycle_mid_year, fit_crosswalk, rogan_gladen
from .paired import expit, logit

Z975 = float(stats.norm.ppf(0.975))
MIN_TRAIN = 3
# Origins up to this cycle choose the crosswalk; later origins only score the choice.
LAST_SELECTION_ORIGIN = "2011-2012"


def candidate_specs(by_sex: bool) -> dict[str, Spec]:
    """The pre specified crosswalk candidates compared out of sample."""
    return {
        "crosswalk_all_cycles": Spec(by_sex=by_sex, trend=False),
        "crosswalk_linear_trend": Spec(by_sex=by_sex, trend=True),
        "crosswalk_latest_3": Spec(by_sex=by_sex, trend=False, window=3),
    }


METHOD_LABELS = {
    "p_self": "No adjustment (self report as is)",
    "rogan_gladen": "Sensitivity and specificity correction, all earlier cycles",
    "rogan_gladen_latest_3": "Sensitivity and specificity correction, latest 3 cycles",
    "crosswalk_all_cycles": "Logit crosswalk, constant, all earlier cycles",
    "crosswalk_linear_trend": "Logit crosswalk, age specific linear trend",
    "crosswalk_latest_3": "Logit crosswalk, constant, latest 3 cycles",
}


def crosswalk_predictions(train: pd.DataFrame, test: pd.DataFrame, spec: Spec) -> pd.DataFrame:
    """Predicted measured prevalence and 95% prediction interval for each held out cell."""
    crosswalk = fit_crosswalk(train, spec)
    cells = test.assign(mid_year=test["cycle"].map(cycle_mid_year))
    d_mean, d_var = crosswalk.predict(cells)
    half = Z975 * np.sqrt(d_var + test["se_d"].to_numpy() ** 2)
    base = logit(test["p_self"].to_numpy())
    return pd.DataFrame(
        {
            "pred": expit(base + d_mean),
            "lower": expit(base + d_mean - half),
            "upper": expit(base + d_mean + half),
        }
    )


def rogan_gladen_predictions(
    train: pd.DataFrame, test: pd.DataFrame, by: Sequence[str], window: int | None = None
) -> np.ndarray:
    """Correct held out self report with training sensitivity and specificity (mean over cycles)."""
    if window is not None:
        train = train[train["cycle"].isin(sorted(train["cycle"].unique())[-window:])]
    se_sp = train.groupby(list(by))[["sens", "spec"]].mean()
    matched = test.join(se_sp, on=list(by), rsuffix="_train")
    return rogan_gladen(matched["p_self"], matched["sens_train"], matched["spec_train"])


def predict_one_origin(paired: pd.DataFrame, by: Sequence[str], origin: str) -> pd.DataFrame:
    """Fit on cycles before `origin`, predict the cells of `origin`."""
    train = paired[paired["cycle"] < origin].reset_index(drop=True)
    test = paired[paired["cycle"] == origin].reset_index(drop=True)
    if train["cycle"].nunique() < MIN_TRAIN or test.empty:
        raise ValueError(f"Origin {origin} needs {MIN_TRAIN} earlier cycles and its own data")
    out = test[["cycle", *by, "p_self", "p_meas"]].copy()
    out["n_train_cycles"] = train["cycle"].nunique()
    out["rogan_gladen"] = rogan_gladen_predictions(train, test, by)
    out["rogan_gladen_latest_3"] = rogan_gladen_predictions(train, test, by, window=3)
    for key, spec in candidate_specs("sex" in by).items():
        pred = crosswalk_predictions(train, test, spec)
        out[key] = pred["pred"].to_numpy()
        out[f"{key}_lower"] = pred["lower"].to_numpy()
        out[f"{key}_upper"] = pred["upper"].to_numpy()
    return out


def rolling_origin(paired: pd.DataFrame, by: Sequence[str]) -> pd.DataFrame:
    """Cell level predictions for every forecast origin with enough earlier cycles."""
    cycles = sorted(paired["cycle"].unique())
    origins = cycles[MIN_TRAIN:]
    return pd.concat([predict_one_origin(paired, by, o) for o in origins], ignore_index=True)


def split_selection_test(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Selection origins (used to pick a crosswalk) and later test origins (used only to report it)."""
    is_selection = predictions["cycle"] <= LAST_SELECTION_ORIGIN
    return predictions[is_selection], predictions[~is_selection]


def score(predictions: pd.DataFrame) -> pd.DataFrame:
    """Bias, mean absolute error, maximum error (percentage points) and interval coverage."""
    truth = predictions["p_meas"].to_numpy()
    rows = []
    for key, label in METHOD_LABELS.items():
        err = 100 * (predictions[key].to_numpy() - truth)
        coverage = np.nan
        if f"{key}_lower" in predictions:
            inside = (truth >= predictions[f"{key}_lower"]) & (truth <= predictions[f"{key}_upper"])
            coverage = float(inside.mean())
        rows.append(
            {
                "method": label,
                "key": key,
                "cells": len(err),
                "bias_pp": float(err.mean()),
                "mae_pp": float(np.abs(err).mean()),
                "max_abs_error_pp": float(np.abs(err).max()),
                "coverage_95": coverage,
            }
        )
    return pd.DataFrame(rows)
