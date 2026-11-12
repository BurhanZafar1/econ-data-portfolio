import numpy as np
import pandas as pd
import pytest

from tsmom import data, instruments as ins

# NYSE/NYMEX holidays needed for the known expiry dates below
HOLIDAYS = pd.to_datetime(["2020-04-10", "2020-05-25", "2020-07-03"])


def _bdays(first, last):
    d = pd.bdate_range(first, last)
    return d[~d.isin(HOLIDAYS)]


def test_par_bond_prices_at_par_and_duration():
    assert np.isclose(ins.par_bond_price(0.05, 10, 0.05), 1.0)
    assert np.isclose(ins.par_bond_price(0.0, 2, 0.0), 1.0)
    num = (ins.par_bond_price(0.05, 10, 0.0499) - ins.par_bond_price(0.05, 10, 0.0501)) / 0.0002
    assert abs(num - ins.modified_duration_par(0.05, 10)) < 1e-4
    assert abs(ins.modified_duration_par(0.05, 10) - 7.7946) < 1e-3  # textbook value


def test_bond_excess_return_is_carry_when_yields_do_not_move():
    idx = pd.bdate_range("2020-01-01", periods=5)
    r = ins.bond_excess_returns(pd.Series(4.0, idx), pd.Series(1.0, idx), 10)
    days = idx.to_series().diff().dt.days.iloc[1:]
    assert np.allclose(r.to_numpy(), 0.03 * days.to_numpy() / 365)


def test_bond_return_sign_follows_yield_change():
    idx = pd.bdate_range("2020-01-01", periods=3)
    r = ins.bond_excess_returns(pd.Series([4.0, 4.5, 4.0], idx), pd.Series([4.0, 4.5, 4.0], idx), 10)
    assert r.iloc[0] < -0.03 and r.iloc[1] > 0.03


@pytest.mark.parametrize("rule,month,expected", [
    ("CL", "2020-04", "2020-04-21"),  # May 2020 WTI, the contract that settled below zero
    ("CL", "2020-05", "2020-05-19"),  # 25th is Memorial Day, so 3 days before Friday 22nd
    ("NG", "2020-04", "2020-04-28"),
    ("HO", "2020-04", "2020-04-30"),
])
def test_known_nymex_last_trading_days(rule, month, expected):
    days = _bdays("2020-03-01", "2020-07-31")
    ltd = ins.last_trade_dates(days, rule)
    assert pd.Timestamp(expected) in ltd
    assert sum(d.strftime("%Y-%m") == month for d in ltd) == 1


def test_roll_reproduces_true_holding_returns():
    """Two synthetic contract series where every contract has a known price path."""
    days = _bdays("2020-01-01", "2020-12-31")
    ltd = ins.last_trade_dates(days, "HO")
    rng = np.random.default_rng(0)
    common = np.cumsum(rng.normal(0, 0.01, len(days)))
    # contract n (expiring at ltd[n]) trades at exp(common + 0.05 * n)
    which = np.searchsorted(ltd.values, days.values)  # index of the front contract each day
    c1 = np.exp(common + 0.05 * which)
    c2 = np.exp(common + 0.05 * (which + 1))
    r = ins.rolled_futures_returns(pd.Series(c1, days), pd.Series(c2, days), "HO")
    true = np.exp(np.diff(common)) - 1.0  # any single contract earns only the common move
    assert np.allclose(r.to_numpy(), true[-len(r):])


def test_roll_dates_match_the_data():
    en = pd.read_csv(data.RAW / "eia_energy_futures_daily.csv.xz", index_col=0, parse_dates=True)
    for code in ("CL", "HO", "NG"):
        share = {o: ins.roll_date_check(en[f"{code}1"], en[f"{code}2"], code, o) for o in (-1, 0, 1)}
        assert share[0] > 0.6 and share[0] > share[-1] + 0.3 and share[0] > share[1] + 0.3
