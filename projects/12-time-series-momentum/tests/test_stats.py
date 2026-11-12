import numpy as np
import statsmodels.api as sm

from tsmom import stats


def _data(seed=0, n=400):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 2))
    g = np.repeat(np.arange(n // 8), 8)
    y = 0.5 + x @ np.array([1.0, -0.5]) + rng.normal(size=n) + rng.normal(size=n // 8)[g]
    return y, x, g


def test_ols_matches_statsmodels_all_covariances():
    y, x, g = _data()
    X = sm.add_constant(x)
    ref = {
        "nonrobust": sm.OLS(y, X).fit(),
        "hc0": sm.OLS(y, X).fit(cov_type="HC0"),
        "nw": sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6, "use_correction": False}),
        "cluster": sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": g}),
    }
    for cov, fit in ref.items():
        ours = stats.ols(y, x, ["a", "b"], cov=cov, lags=6, groups=g)
        assert np.allclose(ours.coef, fit.params)
        assert np.allclose(ours.se, fit.bse, rtol=1e-6), cov
        assert np.isclose(ours.r2, fit.rsquared)


def test_sharpe_and_bootstrap():
    rng = np.random.default_rng(1)
    x = rng.normal(0.01, 0.03, 600)
    assert np.isclose(stats.sharpe(x), x.mean() / x.std(ddof=1) * np.sqrt(12))
    boot = stats.block_bootstrap_sharpe(x, 12, 500, np.random.default_rng(2))
    assert abs(np.median(boot) - stats.sharpe(x)) < 0.15


def test_psr_and_expected_max():
    assert np.isclose(stats.probabilistic_sharpe(0.2, 0.2, 100, 0.0, 3.0), 0.5)
    rng = np.random.default_rng(7)
    mc = rng.normal(0, 0.1, (20000, 50)).max(axis=1).mean()
    assert abs(stats.expected_max_sharpe(0.01, 50) - mc) < 0.01


def test_deflated_sharpe_falls_with_more_trials():
    rng = np.random.default_rng(3)
    x = rng.normal(0.01, 0.04, 300)
    trials = rng.normal(0.0, 0.08, 64)
    d_few, _ = stats.deflated_sharpe(x, trials[:4])
    d_many, _ = stats.deflated_sharpe(x, trials)
    assert d_many < d_few
