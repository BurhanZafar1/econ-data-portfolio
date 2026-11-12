import numpy as np
import pandas as pd

from tsmom import analysis, stats


def test_to_quarterly_compounds_complete_quarters_only():
    idx = pd.period_range("2000-01", "2000-08", freq="M")
    f = pd.DataFrame({"x": [0.01, 0.02, -0.01, 0.0, 0.0, 0.1, 0.05, 0.05]}, index=idx)
    q = analysis.to_quarterly(f)
    assert list(q.index.astype(str)) == ["2000Q1", "2000Q2"]
    assert np.isclose(q.loc[pd.Period("2000Q1", "Q"), "x"], 1.01 * 1.02 * 0.99 - 1)


def test_pooled_lag_regression_alignment():
    """Returns follow r_t = 0.5 r_{t-2} + e_t, so the lag 2 slope is large and lags 1 and 3 are not."""
    rng = np.random.default_rng(0)
    idx = pd.period_range("1980-01", periods=400, freq="M")
    vol = pd.DataFrame(1.0, index=idx, columns=list("abcde"))
    e = rng.normal(size=(400, 5))
    r = np.zeros_like(e)
    for t in range(400):
        r[t] = e[t] + (0.5 * r[t - 2] if t >= 2 else 0.0)
    m = pd.DataFrame(r, index=idx, columns=vol.columns)
    out = analysis.pooled_lag_tstats(m, vol, range(1, 4), first="1981-01", last="2012-12")
    assert out.loc[2, "t"] > 8 and abs(out.loc[1, "t"]) < 3 and abs(out.loc[3, "t"]) < 3
    assert out.loc[2, "nobs"] == 5 * (12 * 32)


def test_deflated_sharpe_is_psr_at_expected_max():
    rng = np.random.default_rng(4)
    x = rng.normal(0.01, 0.04, 300)
    trials = rng.normal(0.0, 0.05, 20)
    dsr, sr0 = stats.deflated_sharpe(x, trials)
    import scipy.stats as st
    psr = stats.probabilistic_sharpe(x.mean() / x.std(ddof=1), sr0, len(x), st.skew(x), st.kurtosis(x, fisher=False))
    assert np.isclose(dsr, psr)
    assert np.isclose(sr0, stats.expected_max_sharpe(np.var(trials, ddof=1), 20))
