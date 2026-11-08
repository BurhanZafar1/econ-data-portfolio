"""Train every LSTM in the project (about 80 minutes on a laptop CPU).

Writes output/lstm_runs.csv (validation accuracies) and output/lstm_predictions.csv.gz
(test probabilities). run.py reads these files, so the LSTMs only need training once.

Run:  python lstm_runs.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from lstm_replication import data, features, lstm, samples, splits  # noqa: E402

OUTPUT = ROOT / "output"
SEEDS = (1, 2, 3, 4, 5)
EXTENSION_SEEDS = (1, 2, 3)


def run() -> None:
    raw = data.load_raw(ROOT / "data" / "raw" / "sp500_daily.csv")
    paper, ext = samples.paper_sample(raw), samples.extension_sample(raw)
    folds = splits.walk_forward(paper.n_train)
    cv_rows, pred_rows = [], []

    def record(sample, variant, model, seed, proba):
        for date, p in zip(sample.test.index, proba):
            pred_rows.append({"variant": variant, "model": model, "seed": seed, "date": date.date(), "proba": float(p)})

    for model, cols in features.FEATURE_SETS.items():
        cfg = lstm.CONFIGS[model]
        Xp, yp = paper.train[cols].to_numpy(), paper.train["label"].to_numpy()
        Xt = paper.test[cols].to_numpy()
        start = time.time()
        dev = lstm.walk_forward_accuracy(cfg, Xp, yp, folds, seed=1, scale=False)
        cv_rows.append({"variant": "replication", "model": model, "seed": 1, "dev_accuracy": dev})
        for seed in SEEDS:
            record(paper, "replication", model, seed, lstm.fit_predict(cfg, Xp, yp, Xt, seed, scale=False))
            record(paper, "scaled", model, seed, lstm.fit_predict(cfg, Xp, yp, Xt, seed, scale=True))
        Xe, ye, Xet = ext.train[cols].to_numpy(), ext.train["label"].to_numpy(), ext.test[cols].to_numpy()
        for seed in EXTENSION_SEEDS:
            record(ext, "extension_replication", model, seed, lstm.fit_predict(cfg, Xe, ye, Xet, seed, scale=False))
            record(ext, "extension_scaled", model, seed, lstm.fit_predict(cfg, Xe, ye, Xet, seed, scale=True))
        OUTPUT.mkdir(exist_ok=True)
        pd.DataFrame(cv_rows).to_csv(OUTPUT / "lstm_runs.csv", index=False)
        pd.DataFrame(pred_rows).to_csv(OUTPUT / "lstm_predictions.csv.gz", index=False, float_format="%.6f")
        print(f"model {model} done in {time.time() - start:.0f}s, dev accuracy {dev:.4f}", flush=True)


if __name__ == "__main__":
    run()
