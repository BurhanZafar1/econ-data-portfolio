"""Known answer tests for the Taylor linearization estimators."""

import math

import numpy as np
import pandas as pd
import pytest

from nhanes_bp.survey import Design, Estimate, estimate, ratio_mean, standardized_mean, taylor_se


def toy_design() -> tuple[np.ndarray, Design]:
    # Two strata, two PSUs each. Worked by hand in the comments below.
    y = np.array([1.0, 0.0, 1.0, 0.0, 0.0, 1.0])
    design = Design(
        weight=np.array([1.0, 1.0, 2.0, 1.0, 1.0, 1.0]),
        stratum=np.array([1, 1, 1, 2, 2, 2]),
        psu=np.array([1, 1, 2, 1, 2, 2]),
    )
    return y, design


def test_ratio_mean_and_se_match_hand_calculation():
    # R = 4/7. PSU totals of z: -1/49, 6/49 | -4/49, -1/49.
    # V = 2*(1/98) + 2*(18/9604) = 58/2401, so SE = sqrt(58)/49.
    y, design = toy_design()
    r, z = ratio_mean(y, np.ones(6, dtype=bool), design)
    assert r == pytest.approx(4 / 7)
    assert taylor_se(z, design) == pytest.approx(math.sqrt(58) / 49)
    assert design.df == 2  # 4 PSUs minus 2 strata


def test_domain_rows_outside_have_zero_influence():
    y, design = toy_design()
    in_domain = np.array([True, True, True, False, False, True])
    r, z = ratio_mean(y, in_domain, design)
    assert r == pytest.approx(4 / 5)  # (1 + 0 + 2 + 1) / (1 + 1 + 2 + 1)
    assert np.all(z[~in_domain] == 0)


def test_constant_outcome_has_zero_variance():
    _, design = toy_design()
    r, z = ratio_mean(np.full(6, 120.0), np.ones(6, dtype=bool), design)
    assert r == 120.0
    assert taylor_se(z, design) == pytest.approx(0.0, abs=1e-12)


def test_direct_standardization_hand_example():
    # Group A mean 10 (weights 1,1), group B mean 30 (weight 2). Standard 25% A, 75% B.
    y = np.array([8.0, 12.0, 30.0, 0.0])
    design = Design(np.array([1.0, 1.0, 2.0, 1.0]), np.array([1, 1, 2, 2]), np.array([1, 2, 1, 2]))
    groups = np.array(["A", "A", "B", "B"])
    in_domain = np.array([True, True, True, False])
    value, _ = standardized_mean(y, in_domain, groups, pd.Series({"A": 0.25, "B": 0.75}), design)
    assert value == pytest.approx(0.25 * 10 + 0.75 * 30)


def test_logit_interval_stays_in_unit_interval_and_contains_estimate():
    est = Estimate(value=0.01, se=0.006, df=15, n=350)
    lo, hi = est.ci_logit
    assert 0 < lo < 0.01 < hi < 1
    sym_lo, _ = est.ci
    assert sym_lo < 0  # the symmetric interval would cross zero here


def test_single_psu_stratum_is_an_error():
    design = Design(np.ones(3), np.array([1, 1, 2]), np.array([1, 2, 1]))
    with pytest.raises(ValueError):
        estimate(ratio_mean(np.ones(3), np.ones(3, dtype=bool), design), design, 3)
