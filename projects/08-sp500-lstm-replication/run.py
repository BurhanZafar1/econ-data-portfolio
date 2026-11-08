"""Reproduce every table, chart and number in the README: python run.py

Fast path (about 1 minute): baselines are refit here; LSTM results are read from
output/lstm_predictions.csv.gz, written by lstm_runs.py (about 80 minutes).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from lstm_replication import baseline, data, evaluate, features, paper, samples, splits  # noqa: E402
from lstm_replication import report  # noqa: E402

OUTPUT = ROOT / "output"


def baseline_results(paper_sample: samples.Sample, ext: samples.Sample) -> pd.DataFrame:
    """Original folds, purged folds, and the frozen spec on 2019 to 2026."""
    rows = []
    n = paper_sample.n_train
    y_test = paper_sample.test["label"].to_numpy()
    y_ext = ext.test["label"].to_numpy()
    for model, cols in features.FEATURE_SETS.items():
        X, y = paper_sample.train[cols], paper_sample.train["label"]
        for folds_name, folds in (
            ("original", splits.walk_forward(n)),
            ("purged", splits.purged_walk_forward(n, purge=features.HORIZON)),
        ):
            fit = baseline.fit(model, X, y, folds)
            proba = fit.estimator.predict_proba(paper_sample.test[cols])[:, 1]
            rows.append(
                {"model": model, "variant": f"baseline_{folds_name}", "dev_accuracy": fit.dev_accuracy,
                 "penalty": fit.params["penalty"], "alpha": fit.params["alpha"], "l1_ratio": fit.params["l1_ratio"],
                 "n_selected": fit.n_selected, **evaluate.summary(y_test, proba),
                 **evaluate.bootstrap_ci(y_test, proba, seed=model)}
            )
            if folds_name == "original" and model == baseline.RANDOM_SEARCH_MODEL:
                fixed = baseline.refit_fixed(baseline.PAPER_MODEL3_PARAMS, X, y)
                p_fixed = fixed.predict_proba(paper_sample.test[cols])[:, 1]
                rows.append({"model": model, "variant": "baseline_paper_params", **baseline.PAPER_MODEL3_PARAMS,
                             "n_selected": int((fixed.named_steps["logistic"].coef_ != 0).sum()),
                             **evaluate.summary(y_test, p_fixed)})
            if folds_name == "original":
                frozen = baseline.refit_fixed(fit.params, ext.train[cols], ext.train["label"])
                p_ext = frozen.predict_proba(ext.test[cols])[:, 1]
                rows.append({"model": model, "variant": "baseline_extension", **evaluate.summary(y_ext, p_ext),
                             **evaluate.bootstrap_ci(y_ext, p_ext, seed=model)})
    return pd.DataFrame(rows)


def lstm_results(paper_sample: samples.Sample, ext: samples.Sample) -> pd.DataFrame:
    """Per model and variant: metrics of each seed, and of the seed average (ensemble)."""
    preds = pd.read_csv(OUTPUT / "lstm_predictions.csv.gz", parse_dates=["date"])
    cv = pd.read_csv(OUTPUT / "lstm_runs.csv")
    labels = pd.concat([paper_sample.test["label"], ext.test["label"]])
    labels = labels[~labels.index.duplicated()]
    rows = []
    for (variant, model), group in preds.groupby(["variant", "model"]):
        wide = group.pivot(index="date", columns="seed", values="proba").sort_index()
        y = labels.loc[wide.index].to_numpy()
        per_seed = [evaluate.summary(y, wide[s].to_numpy()) for s in wide.columns]
        ensemble = wide.mean(axis=1).to_numpy()
        dev = cv.loc[(cv.variant == variant) & (cv.model == model), "dev_accuracy"]
        rows.append(
            {"model": model, "variant": f"lstm_{variant}", "n_seeds": wide.shape[1],
             "dev_accuracy": float(dev.iloc[0]) if len(dev) else np.nan,
             "seed1_accuracy": per_seed[0]["accuracy"], "seed1_auc": per_seed[0]["auc"],
             "accuracy_min": min(r["accuracy"] for r in per_seed), "accuracy_max": max(r["accuracy"] for r in per_seed),
             "auc_min": min(r["auc"] for r in per_seed), "auc_max": max(r["auc"] for r in per_seed),
             **evaluate.summary(y, ensemble), **evaluate.bootstrap_ci(y, ensemble, seed=model)}
        )
    return pd.DataFrame(rows)


def sanity_checks(paper_sample: samples.Sample, raw_rows: int, results: pd.DataFrame) -> list[str]:
    checks = []

    def check(condition: bool, text: str) -> None:
        if not condition:
            raise AssertionError(text)
        checks.append(text)

    check(raw_rows == paper.RAW_ROWS, f"paper window has {paper.RAW_ROWS} raw rows, as in the notebook")
    check(len(paper_sample.table) == paper.FEATURE_ROWS, f"{paper.FEATURE_ROWS} rows after features, as in the notebook")
    check(len(paper_sample.test) == 946, "946 test days, as in the report")
    check(abs(paper_sample.test["label"].mean() - paper.TEST_UP_SHARE) < 1e-12, "test labels match the notebook exactly")
    check(abs(paper_sample.train["label"].mean() - paper.TRAIN_UP_SHARE) < 1e-12, "training labels match the notebook exactly")
    check(str(paper_sample.table.index[0].date()) == "1981-07-31", "feature table starts 31 Jul 1981, as in the notebook")
    inside = results.dropna(subset=["auc_lo"])
    check(bool(((inside.auc >= inside.auc_lo - 1e-9) & (inside.auc <= inside.auc_hi + 1e-9)).all()),
          "every AUC lies inside its bootstrap interval")
    return checks


def main() -> None:
    raw = data.load_raw(ROOT / "data" / "raw" / "sp500_daily.csv")
    raw_rows = len(data.window(raw, data.PAPER_START, data.PAPER_END))
    paper_sample, ext = samples.paper_sample(raw), samples.extension_sample(raw)
    OUTPUT.mkdir(exist_ok=True)
    results = pd.concat([baseline_results(paper_sample, ext), lstm_results(paper_sample, ext)], ignore_index=True)
    results.to_csv(OUTPUT / "results.csv", index=False, float_format="%.4f")
    checks = sanity_checks(paper_sample, raw_rows, results)
    headline = report.write_all(results, paper_sample, ext, OUTPUT)
    headline["checks_passed"] = checks
    (OUTPUT / "headline.json").write_text(json.dumps(headline, indent=2))
    print(json.dumps(headline, indent=2))


if __name__ == "__main__":
    main()
