"""Logistic regression baselines, configured as in the original notebook.

Pipeline: StandardScaler then SGDClassifier(log loss, shuffle=False, tol=1e-3, random_state=1).
Penalty (l1, l2, elastic net), alpha and l1_ratio are tuned by grid search (random search for
model 3) over 9 walk forward folds, and the best setting by mean validation accuracy is refit
on the whole training set.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import uniform
from sklearn.base import BaseEstimator
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, make_scorer
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

L1_RATIOS = [0, 0.2, 0.4, 0.6, 0.8, 1]
PENALTIES = ["l1", "l2", "elasticnet"]
# model: (alpha grid, max_iter) from the notebook; model 3 uses random search instead.
GRIDS: dict[int, tuple[list[float], int]] = {
    1: ([0.0011, 0.0013, 0.0014], 8),
    2: ([0.0011, 0.0012, 0.0013], 8),
    4: ([0.0011, 0.0012, 0.0013], 8),
    5: ([0.0001, 0.0003, 0.0005], 10),
    6: ([0.0011, 0.0012, 0.0013], 8),
    7: ([0.0019, 0.002, 0.0021], 10),
}
RANDOM_SEARCH_MODEL = 3
RANDOM_SEARCH_ITER = 20
RANDOM_SEARCH_MAX_ITER = 20  # printed by the notebook as "Number of iterations: 20"
# The setting the notebook's random search picked for model 3 (cell 65 output).
PAPER_MODEL3_PARAMS = {"alpha": 1.836230045470262e-05, "l1_ratio": 0.9168613345297285, "penalty": "l1", "max_iter": 20}


@dataclass
class BaselineFit:
    model: int
    dev_accuracy: float
    params: dict
    estimator: BaseEstimator
    n_selected: int


def pipeline() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "logistic",
                SGDClassifier(loss="log_loss", shuffle=False, early_stopping=False, tol=1e-3, random_state=1),
            ),
        ]
    )


def search(model: int, folds) -> BaseEstimator:
    scoring = {"AUC": "roc_auc", "accuracy": make_scorer(accuracy_score)}
    if model == RANDOM_SEARCH_MODEL:
        space = {
            "logistic__alpha": uniform(loc=0.00001, scale=0.0001),
            "logistic__l1_ratio": uniform(loc=0, scale=1),
            "logistic__penalty": PENALTIES,
            "logistic__max_iter": [RANDOM_SEARCH_MAX_ITER],
        }
        return RandomizedSearchCV(
            pipeline(), space, n_iter=RANDOM_SEARCH_ITER, random_state=1, cv=folds, scoring=scoring, refit="accuracy"
        )
    alphas, max_iter = GRIDS[model]
    grid = {
        "logistic__alpha": alphas,
        "logistic__l1_ratio": L1_RATIOS,
        "logistic__penalty": PENALTIES,
        "logistic__max_iter": [max_iter],
    }
    return GridSearchCV(pipeline(), grid, cv=folds, scoring=scoring, refit="accuracy")


def fit(model: int, X: pd.DataFrame, y: pd.Series, folds) -> BaselineFit:
    """Tune on the walk forward folds and refit the best setting on all of X."""
    with warnings.catch_warnings():
        # max_iter is deliberately tiny (8 to 20 epochs) in the original, so SGD stops early.
        warnings.simplefilter("ignore", ConvergenceWarning)
        tuned = search(model, list(folds)).fit(X, y)
    coef = tuned.best_estimator_.named_steps["logistic"].coef_
    params = {k.replace("logistic__", ""): v for k, v in tuned.best_params_.items()}
    return BaselineFit(model, float(tuned.best_score_), params, tuned.best_estimator_, int(np.count_nonzero(coef)))


def refit_fixed(params: dict, X: pd.DataFrame, y: pd.Series) -> BaseEstimator:
    """Refit a frozen specification (used for the out of sample extension)."""
    estimator = pipeline().set_params(**{f"logistic__{k}": v for k, v in params.items()})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        return estimator.fit(X, y)
