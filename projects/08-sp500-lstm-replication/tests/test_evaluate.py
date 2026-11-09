"""Tests for the metrics and the bootstrap."""

import numpy as np
import pytest

from lstm_replication import evaluate


def test_constant_scores_have_auc_half():
    y = np.array([0, 1, 1, 0, 1])
    assert evaluate.auc(y, np.full(5, 0.7)) == 0.5


def test_perfect_scores_have_auc_one():
    y = np.array([0, 0, 1, 1])
    assert evaluate.auc(y, np.array([0.1, 0.2, 0.8, 0.9])) == 1.0


def test_always_up_rule():
    y = np.array([1, 1, 1, 0])
    s = evaluate.summary(y, np.full(4, 0.9))
    assert s["accuracy"] == s["always_up"] == 0.75
    assert s["share_pred_up"] == 1.0


def test_block_bootstrap_keeps_blocks_contiguous():
    rng = np.random.default_rng(0)
    idx = evaluate.block_bootstrap_indices(100, 10, rng)
    assert len(idx) == 100
    assert all(np.all(np.diff(idx[i : i + 10]) == 1) for i in range(0, 100, 10))


def test_bootstrap_interval_is_wide_for_pure_noise():
    rng = np.random.default_rng(1)
    y = (rng.random(600) < 0.6).astype(int)
    p = rng.random(600)
    ci = evaluate.bootstrap_ci(y, p, n_boot=300)
    assert ci["auc_lo"] < 0.5 < ci["auc_hi"]


def test_bootstrap_detects_real_signal():
    rng = np.random.default_rng(2)
    y = (rng.random(600) < 0.5).astype(int)
    p = np.clip(0.5 + 0.3 * (y - 0.5) + 0.1 * rng.standard_normal(600), 0, 1)
    ci = evaluate.bootstrap_ci(y, p, n_boot=300)
    assert ci["auc_lo"] > 0.5
