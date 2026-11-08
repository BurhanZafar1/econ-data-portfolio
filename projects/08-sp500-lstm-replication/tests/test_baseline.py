"""Known answer tests against the paper's Table 1.

Exact to the reported digit: dev and test accuracy for models 1, 2 and 5; test accuracy for
models 4, 6 and 7. Dev accuracy for models 4, 6 and 7 differs by at most 0.1 point (a handful
of validation days), which we attribute to small numerical differences in SGD between
scikit-learn 0.20 (2019) and today; the selected hyperparameters are the same.
"""

from pathlib import Path

import pytest
from sklearn.metrics import accuracy_score

from lstm_replication import baseline, data, features, paper, samples, splits

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "sp500_daily.csv"


@pytest.fixture(scope="module")
def sample():
    return samples.paper_sample(data.load_raw(RAW))


@pytest.mark.parametrize("model,dev_tol", [(1, 0), (2, 0), (5, 0), (4, 0.001), (6, 0.001), (7, 0.001)])
def test_baseline_matches_table1(sample, model, dev_tol):
    cols = features.FEATURE_SETS[model]
    fit = baseline.fit(model, sample.train[cols], sample.train["label"], splits.walk_forward(sample.n_train))
    test_acc = accuracy_score(sample.test["label"], fit.estimator.predict(sample.test[cols]))
    assert round(test_acc, 4) == paper.TABLE1[model][3]
    assert abs(round(fit.dev_accuracy, 4) - paper.TABLE1[model][2]) <= dev_tol + 1e-9


def test_model1_matches_notebook_printout(sample):
    cols = features.FEATURE_SETS[1]
    fit = baseline.fit(1, sample.train[cols], sample.train["label"], splits.walk_forward(sample.n_train))
    assert fit.params["penalty"] == "l2" and fit.params["alpha"] == 0.0014
    assert fit.dev_accuracy == pytest.approx(0.5448412698412698, abs=1e-12)  # notebook cell 39


def test_model3_with_paper_hyperparameters(sample):
    """Model 3 used a random search; with the hyperparameters the notebook printed, the
    refit model reproduces the paper's test accuracy, AUC and 6 selected features exactly."""
    from lstm_replication import evaluate

    cols = features.FEATURE_SETS[3]
    est = baseline.refit_fixed(baseline.PAPER_MODEL3_PARAMS, sample.train[cols], sample.train["label"])
    proba = est.predict_proba(sample.test[cols])[:, 1]
    assert round(accuracy_score(sample.test["label"], (proba > 0.5).astype(int)), 4) == paper.TABLE1[3][3]
    assert round(evaluate.auc(sample.test["label"].to_numpy(), proba), 2) == paper.TABLE1[3][5]
    assert int((est.named_steps["logistic"].coef_ != 0).sum()) == 6
