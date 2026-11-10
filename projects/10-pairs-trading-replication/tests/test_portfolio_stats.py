import numpy as np
import pandas as pd
import statsmodels.api as sm

from pairs import paper, portfolio, stats


def test_six_overlapping_strategies_and_zero_on_flat_prices():
    idx = pd.bdate_range("2000-01-03", "2003-12-31")
    rng = np.random.default_rng(5)
    r = pd.DataFrame(rng.normal(0, 0.01, (len(idx), 8)), index=idx)
    res = portfolio.run(r, "2001-07", "2003-06", portfolio.Config(top=3))
    assert (res.monthly["n_active"] == 6).all()
    assert len(res.monthly) == 24
    flat = pd.DataFrame(0.0, index=idx, columns=range(8))
    flat.iloc[:, 0] = 1e-6  # break ties without moving prices meaningfully
    out = portfolio.run(flat, "2001-07", "2003-06", portfolio.Config(top=3)).monthly
    assert np.allclose(out["committed"], 0.0, atol=1e-6)


def test_newey_west_matches_statsmodels():
    rng = np.random.default_rng(6)
    x = np.cumsum(rng.normal(0, 1, 400)) * 0.01 + rng.normal(0, 1, 400)
    fit = sm.OLS(x, np.ones_like(x)).fit(cov_type="HAC", cov_kwds={"maxlags": 6, "use_correction": False})
    assert np.isclose(stats.newey_west_se(x, 6), fit.bse[0], rtol=1e-10)


def test_psr_and_expected_max():
    assert np.isclose(stats.probabilistic_sharpe(0.2, 0.2, 100, 0.0, 3.0), 0.5)
    assert stats.expected_max_sharpe(0.01, 10) < stats.expected_max_sharpe(0.01, 100)
    # Monte Carlo check of the expected maximum of 50 normal Sharpe ratios
    rng = np.random.default_rng(7)
    mc = rng.normal(0, 0.1, (20000, 50)).max(axis=1).mean()
    assert abs(stats.expected_max_sharpe(0.01, 50) - mc) < 0.01


def test_paper_implied_cost_known_answer():
    # GGR section 3.3: 1.44% to 0.90% a month, two round trips per six months -> 162 bp
    assert round(1e4 * paper.implied_round_trip_cost(0.0144, 0.0090, 2.0)) == paper.IMPLIED_COST_BP_PER_ROUND_TRIP


def test_paper_table1_internally_consistent():
    for panel in paper.TABLE1.values():
        for full, se, t, committed in panel.values():
            assert abs(full / se - t) < 0.05
            assert committed < full


def test_paper_window_has_474_months():
    months = pd.period_range(*paper.SAMPLE, freq="M")
    assert len(months) == paper.N_MONTHS


def test_portfolio_has_no_look_ahead():
    # rewriting every return after June 2002 must not change any monthly return up to June 2002
    idx = pd.bdate_range("2000-01-03", "2003-12-31")
    rng = np.random.default_rng(8)
    r = pd.DataFrame(rng.normal(0, 0.01, (len(idx), 12)), index=idx)
    alt = r.copy()
    late = alt.index > "2002-06-30"
    alt.loc[late] = rng.normal(0, 0.03, (late.sum(), 12))
    for wait in (0, 1):
        cfg = portfolio.Config(top=4, wait=wait)
        a = portfolio.run(r, "2001-07", "2003-06", cfg).monthly
        b = portfolio.run(alt, "2001-07", "2003-06", cfg).monthly
        keep = a.index <= pd.Period("2002-06", "M")
        assert np.allclose(a.loc[keep, "committed"], b.loc[keep, "committed"])
        assert not np.allclose(a.loc[~keep, "committed"], b.loc[~keep, "committed"])
