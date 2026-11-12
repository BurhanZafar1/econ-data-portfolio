import numpy as np
import pandas as pd

from tsmom import data


def test_instrument_set_and_coverage():
    daily, classes = data.daily_excess_returns()
    assert len(daily) == 23
    counts = pd.Series(classes).value_counts().to_dict()
    assert counts == {"EQ": 4, "FI": 7, "FX": 9, "CM": 3}
    for name, r in daily.items():
        assert r.index.is_monotonic_increasing and r.index.is_unique, name
        assert r.abs().max() < 0.5, name  # no data errors masquerading as returns
        assert r.index[-1] <= pd.Timestamp("2026-10-31"), name


def test_eur_splice_is_continuous():
    fx = pd.read_csv(data.RAW / "fx_usd_per_unit_daily.csv.xz", index_col=0, parse_dates=True)
    dem = fx["DEM"].dropna().iloc[-1] * 1.95583
    eur = fx["EUR"].dropna().iloc[0]
    assert abs(np.log(eur / dem)) < 0.03  # end of 1998 DEM vs first euro quote


def test_factors():
    ff = data.factors()
    assert {"SMB", "HML", "UMD", "RF", "MKT"} <= set(ff.columns)
    w = ff.loc["1985-01":"2009-12"]
    assert w["MKT"].notna().all()
    assert abs(w["MKT"].std() * np.sqrt(12) - 0.15) < 0.04
