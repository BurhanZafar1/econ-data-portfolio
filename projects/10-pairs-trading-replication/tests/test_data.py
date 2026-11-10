import numpy as np
import pandas as pd

from pairs import data


def test_industries_survivorship_free_panel():
    r = data.industry_returns()
    assert r.shape[1] == 49
    assert r.index.min() == pd.Timestamp("1961-01-03")
    assert r.loc["1971-04-01":].notna().all().all()
    assert r.abs().max().max() < 1.0


def test_stocks_and_membership():
    s = data.stock_returns()
    mem = data.membership()
    assert s.shape[1] >= 495
    mask = data.member_on(mem, s.columns, pd.Timestamp("2010-01-04"))
    assert 200 < mask.sum() < 500
    assert "AAPL" in set(s.columns[mask])


def test_etfs():
    e = data.etf_returns()
    assert list(e.columns) == ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
    assert e.notna().all().all() and np.isfinite(e.to_numpy()).all()


def test_stock_universe_is_point_in_time():
    # a stock enters the universe only once it is an index member
    s = data.stock_returns()
    mem = data.membership()
    first = mem.groupby("ticker")["start_date"].min()
    late = first[first > pd.Timestamp("2020-01-01")].index.intersection(s.columns)
    assert len(late) > 0
    mask = data.member_on(mem, s.columns, pd.Timestamp("2010-01-04"))
    assert not set(s.columns[mask]) & set(late)
    # no stored return precedes a stock's first entry date
    for t in late[:20]:
        assert s.loc[: first[t] - pd.Timedelta(days=1), t].isna().all()
