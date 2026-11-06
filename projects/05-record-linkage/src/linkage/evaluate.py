"""Decision rules and their scores against the known true links."""

from __future__ import annotations

import numpy as np
import pandas as pd


def one_to_one(scores: pd.Series) -> pd.MultiIndex:
    """Greedy one to one assignment: take pairs from the highest score down,
    skipping any pair whose A or B record is already linked.

    Used when each entity appears at most once per file.
    """
    ordered = scores.sort_values(ascending=False, kind="stable")
    used_a: set[str] = set()
    used_b: set[str] = set()
    kept = []
    for a, b in ordered.index:
        if a not in used_a and b not in used_b:
            kept.append((a, b))
            used_a.add(a)
            used_b.add(b)
    return pd.MultiIndex.from_tuples(kept, names=["a", "b"])


def exact_rule(left: pd.DataFrame, right: pd.DataFrame, fields: list[str]) -> pd.MultiIndex:
    """The naive merge: link pairs that agree exactly on every listed field."""
    keys_left = left[fields].dropna().reset_index(names="a")
    keys_right = right[fields].dropna().reset_index(names="b")
    joined = keys_left.merge(keys_right, on=fields)
    return pd.MultiIndex.from_frame(joined[["a", "b"]])


def score_links(predicted: pd.MultiIndex, truth: pd.MultiIndex) -> dict[str, float]:
    """Counts, precision, recall and F1 of a set of predicted links."""
    true_positive = len(predicted.intersection(truth))
    false_positive = len(predicted) - true_positive
    precision = true_positive / len(predicted) if len(predicted) else float("nan")
    recall = true_positive / len(truth)
    f1 = 2 * precision * recall / (precision + recall) if true_positive else 0.0
    return {
        "links": len(predicted),
        "true_links_found": true_positive,
        "false_links": false_positive,
        "missed_links": len(truth) - true_positive,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def threshold_curve(posterior: pd.Series, truth: pd.MultiIndex,
                    thresholds: np.ndarray) -> pd.DataFrame:
    """Precision and recall when every pair above each posterior threshold is linked.

    Also reports the precision the model itself predicts, the mean posterior of
    the accepted pairs, which needs no labels.
    """
    is_true = posterior.index.isin(truth)
    values = posterior.to_numpy()
    rows = []
    for threshold in thresholds:
        accepted = values >= threshold
        n_accepted = int(accepted.sum())
        found = int((accepted & is_true).sum())
        rows.append({
            "threshold": float(threshold),
            "links": n_accepted,
            "precision": found / n_accepted if n_accepted else np.nan,
            "model_precision": float(values[accepted].mean()) if n_accepted else np.nan,
            "recall": found / len(truth),
        })
    return pd.DataFrame(rows)
