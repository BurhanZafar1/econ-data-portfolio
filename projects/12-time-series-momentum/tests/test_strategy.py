import numpy as np
import pandas as pd

from tsmom import strategy


def _panel(seed=1, n_months=60, n=4):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2000-01-03", periods=21 * n_months)
    daily = {f"a{i}": pd.Series(rng.normal(0.0002, 0.01 * (i + 1), len(idx)), idx) for i in range(n)}
    return daily


def test_ewma_vol_center_of_mass_and_level():
    delta = strategy.CENTER_OF_MASS / (1 + strategy.CENTER_OF_MASS)
    w = (1 - delta) * delta ** np.arange(5000)
    assert np.isclose((w * np.arange(5000)).sum(), 60.0, atol=1e-6)
    r = pd.Series(np.random.default_rng(3).normal(0, 0.01, 20000))
    v = strategy.ewma_vol(r)
    assert abs(v.iloc[-5000:].mean() - 0.01 * np.sqrt(261)) < 0.01


def test_positions_do_not_use_future_returns():
    daily = _panel()
    m, v = strategy.monthly_panel(daily)
    p = strategy.positions(m, v)
    cut = pd.Timestamp("2003-06-30")
    changed = {k: s.where(s.index <= cut, s * -3.0 + 0.01) for k, s in daily.items()}
    m2, v2 = strategy.monthly_panel(changed)
    p2 = strategy.positions(m2, v2)
    last = pd.Period("2003-06", "M")
    pd.testing.assert_frame_equal(p.loc[:last], p2.loc[:last])


def test_eq5_by_hand():
    daily = _panel(n=2)
    m, v = strategy.monthly_panel(daily)
    inst = strategy.strategy_returns(m, strategy.positions(m, v))
    t = pd.Period("2003-02", "M")
    s = "a1"
    past = np.prod(1 + m[s].loc[t - 12 : t - 1]) - 1  # months t-12 .. t-1, signal known at end of t-1
    expected = np.sign(past) * 0.40 / v[s].loc[t - 1] * m[s].loc[t]
    assert np.isclose(inst[s].loc[t], expected)
    port = strategy.portfolio(inst)
    assert np.isclose(port.loc[t], inst.loc[t].mean())


def test_holding_period_averages_signals_and_uses_current_volatility():
    daily = _panel(n=1)
    m, v = strategy.monthly_panel(daily)
    p = strategy.positions(m, v, k=3, h=3)
    signs = np.sign(strategy.trailing_return(m, 3))
    t = pd.Period("2002-06", "M")
    expected = (signs.loc[t] + signs.loc[t - 1] + signs.loc[t - 2]) / 3 * 0.40 / v.loc[t]
    assert np.allclose(p.loc[t], expected)
    r = strategy.strategy_returns(m, p)
    assert np.allclose(r.loc[t + 1], p.loc[t] * m.loc[t + 1])


def test_expanding_vol_has_no_timing():
    r = pd.Series(np.random.default_rng(5).normal(0, 0.01, 3000))
    v = strategy.expanding_vol(r)
    assert np.isclose(v.iloc[-1], r.std(ddof=1) * np.sqrt(261))


def test_turnover_and_costs():
    pos = pd.DataFrame({"a": [1.0, 1.0, -1.0], "b": [2.0, 1.0, 1.0]}, index=pd.period_range("2000-01", periods=3, freq="M"))
    assert np.allclose(strategy.turnover(pos).to_numpy(), [0.5, 1.0])
    gross = pd.Series([0.01, 0.01, 0.01], index=pos.index)
    net = strategy.net_of_costs(gross, pos, 0.001)
    assert np.allclose(net.to_numpy(), [0.01, 0.01, 0.01 - 0.0005])
