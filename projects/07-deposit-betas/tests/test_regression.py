"""Known answer tests for OLS, the Newey-West covariance and the lag model."""

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from deposit_beta.regression import estimate_pass_through, lag_design, newey_west_lags, ols_hac


def test_hac_hand_calculation_intercept_only():
    # y = 1..4, mean 2.5, residuals -1.5, -0.5, 0.5, 1.5.
    # gamma0 = 5, gamma1 = 1.25, Bartlett weight at lag 1 = 0.5 -> meat = 5 + 2 * 0.5 * 1.25 = 6.25.
    # cov = (1/4) * 6.25 * (1/4) * 4 / (4 - 1) = 0.520833...
    fit = ols_hac(np.array([1.0, 2, 3, 4]), np.ones((4, 1)), ("const",), lags=1)
    assert fit.params[0] == pytest.approx(2.5)
    assert fit.cov[0, 0] == pytest.approx(6.25 / 16 * 4 / 3)


def test_newey_west_rule_of_thumb():
    assert newey_west_lags(100) == 4
    assert newey_west_lags(66) == 3
    assert newey_west_lags(201) == 4


def test_matches_statsmodels_hac():
    rng = np.random.default_rng(0)
    n = 150
    x = np.column_stack([np.ones(n), rng.normal(size=(n, 3))])
    e = np.convolve(rng.normal(size=n + 2), [1, 0.6, 0.3], mode="valid")  # autocorrelated errors
    y = x @ np.array([0.5, 1.0, -2.0, 0.3]) + e
    ours = ols_hac(y, x, ("c", "a", "b", "d"), lags=4)
    ref = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": 4, "use_correction": True})
    np.testing.assert_allclose(ours.params, ref.params, rtol=1e-10)
    np.testing.assert_allclose(ours.cov, ref.cov_params(), rtol=1e-8)
    assert ours.r_squared == pytest.approx(ref.rsquared)


def test_lag_design_splits_signs():
    d_ff = pd.Series([0.25, -0.5, 0.0])
    design = lag_design(d_ff, max_lag=1)
    assert design["up_0"].tolist() == [0.25, 0.0, 0.0]
    assert design["down_0"].tolist() == [0.0, -0.5, 0.0]
    assert design["up_1"].tolist()[1:] == [0.25, 0.0]


def test_recovers_known_asymmetric_betas_without_noise():
    rng = np.random.default_rng(1)
    n = 120
    d_ff = pd.Series(rng.choice([-0.25, 0.0, 0.0, 0.25, 0.5], size=n))
    design = lag_design(d_ff, 2)
    up, down = np.array([0.10, 0.20, 0.05]), np.array([0.05, 0.02, 0.0])
    y = design[["up_0", "up_1", "up_2"]].to_numpy() @ up + design[["down_0", "down_1", "down_2"]].to_numpy() @ down
    changes = pd.DataFrame({"d_fedfunds": d_ff, "d_cd_12m": y})
    fit = estimate_pass_through(changes, "cd_12m", pd.Series(True, index=d_ff.index), "sim", 2)
    assert fit.nobs == n - 2
    np.testing.assert_allclose(fit.up_lags, up, atol=1e-10)
    np.testing.assert_allclose(fit.down_lags, down, atol=1e-10)
    assert fit.beta_up == pytest.approx(0.35)
    assert fit.beta_down == pytest.approx(0.07)
    assert fit.asym_diff == pytest.approx(0.28)
