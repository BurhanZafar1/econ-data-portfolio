"""Tests for the survey design tools."""

import numpy as np
import pandas as pd
import pytest

from sbp_paf.survey import rao_wu_weights, taylor_se_mean


def simulated_design(seed: int = 7) -> pd.DataFrame:
    """15 strata x 2 PSUs, like NHANES, with PSU level clustering in y."""
    rng = np.random.default_rng(seed)
    rows = []
    for h in range(15):
        for p in (1, 2):
            effect = rng.normal(0, 4)
            for _ in range(120):
                rows.append({"stratum": h, "psu": p, "wt_mec": rng.uniform(500, 3000),
                             "y": 125 + effect + rng.normal(0, 15)})
    return pd.DataFrame(rows)


def test_taylor_se_known_answer_two_psus():
    # One stratum, two PSUs of one person each, equal weights: mean 3, z = (-0.5, +0.5),
    # V = 2/1 * (0.25 + 0.25) = 1, so SE = 1.
    y = np.array([2.0, 4.0])
    mean, se = taylor_se_mean(y, np.ones(2), np.ones(2, bool), np.array([1, 1]), np.array([1, 2]))
    assert mean == pytest.approx(3.0)
    assert se == pytest.approx(1.0)


def test_rao_wu_multipliers_are_zero_or_two_with_two_psus():
    design = simulated_design()
    reps = rao_wu_weights(design, 50, np.random.default_rng(3))
    mult = reps / design["wt_mec"].to_numpy()[:, None]
    assert set(np.unique(np.round(mult, 12))) <= {0.0, 2.0}
    # Within a stratum exactly one PSU is kept in each replicate.
    first = design["stratum"] == 0
    kept = pd.DataFrame(mult[first.to_numpy()]).groupby(design.loc[first, "psu"].to_numpy()).max()
    assert (kept.sum(axis=0) == 2.0).all()


def test_bootstrap_se_close_to_taylor_se():
    design = simulated_design()
    y, w = design["y"].to_numpy(), design["wt_mec"].to_numpy()
    _, se_taylor = taylor_se_mean(y, w, np.ones(len(y), bool), design["stratum"].to_numpy(), design["psu"].to_numpy())
    reps = rao_wu_weights(design, 4000, np.random.default_rng(11))
    boot_means = (reps * y[:, None]).sum(axis=0) / reps.sum(axis=0)
    assert boot_means.std(ddof=1) == pytest.approx(se_taylor, rel=0.08)


def test_single_psu_stratum_is_rejected():
    design = pd.DataFrame({"stratum": [1, 1], "psu": [1, 1], "wt_mec": [1.0, 1.0]})
    with pytest.raises(ValueError):
        rao_wu_weights(design, 5, np.random.default_rng(0))


def test_rao_wu_with_three_psus():
    # n_h = 3: two PSUs drawn with replacement, multiplier 1.5 x count, so values in {0, 1.5, 3}
    # and the multipliers of the three PSUs sum to 3 in every replicate.
    design = pd.DataFrame({"stratum": [1, 1, 1], "psu": [1, 2, 3], "wt_mec": [1.0, 1.0, 1.0]})
    reps = rao_wu_weights(design, 200, np.random.default_rng(5))
    assert set(np.unique(reps)) <= {0.0, 1.5, 3.0}
    np.testing.assert_allclose(reps.sum(axis=0), 3.0)
