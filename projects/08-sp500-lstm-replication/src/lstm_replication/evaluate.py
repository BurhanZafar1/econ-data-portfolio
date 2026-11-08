"""Test set metrics with honest uncertainty for overlapping monthly labels."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score

BLOCK = 63  # three label horizons, so bootstrap blocks keep the overlap structure
N_BOOT = 2000


def auc(y: np.ndarray, p: np.ndarray) -> float:
    """ROC AUC; 0.5 when the scores are constant or only one class is present."""
    if np.unique(y).size < 2 or np.unique(p).size < 2:
        return 0.5
    return float(roc_auc_score(y, p))


def block_bootstrap_indices(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    """Moving block bootstrap: concatenate random contiguous blocks until n rows."""
    starts = rng.integers(0, n - block + 1, size=int(np.ceil(n / block)))
    return np.concatenate([np.arange(s, s + block) for s in starts])[:n]


def bootstrap_ci(
    y: np.ndarray, p: np.ndarray, seed: int = 0, block: int = BLOCK, n_boot: int = N_BOOT
) -> dict[str, float]:
    """95% intervals for AUC and for accuracy minus the always up rule, by block bootstrap."""
    rng = np.random.default_rng(seed)
    pred = (p > 0.5).astype(int)
    aucs, edges = [], []
    for _ in range(n_boot):
        idx = block_bootstrap_indices(len(y), block, rng)
        yb, pb = y[idx], p[idx]
        aucs.append(auc(yb, pb))
        edges.append(accuracy_score(yb, pred[idx]) - yb.mean())
    return {
        "auc_lo": float(np.percentile(aucs, 2.5)),
        "auc_hi": float(np.percentile(aucs, 97.5)),
        "edge_lo": float(np.percentile(edges, 2.5)),
        "edge_hi": float(np.percentile(edges, 97.5)),
        "p_auc_le_half": float(np.mean(np.array(aucs) <= 0.5)),
    }


def summary(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    """Point metrics: accuracy, AUC, always up accuracy, share predicted up, and non overlapping AUC."""
    y = np.asarray(y)
    p = np.asarray(p)
    pred = (p > 0.5).astype(int)
    monthly = np.arange(0, len(y), 21)  # one label per month, so the labels do not overlap
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "auc": auc(y, p),
        "always_up": float(y.mean()),
        "share_pred_up": float(pred.mean()),
        "auc_monthly": auc(y[monthly], p[monthly]),
        "n_monthly": int(monthly.size),
    }
