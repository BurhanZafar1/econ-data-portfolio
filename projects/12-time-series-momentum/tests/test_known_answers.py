"""Known answer tests against the paper, using the authors' own factor returns (AQR file)."""

import numpy as np
import pytest

from tsmom import analysis, data, paper, stats

pytestmark = pytest.mark.skipif(not (data.AQR_DIR / "aqr_tsmom_original.xlsx").exists(),
                                reason="run get_data.py first (AQR files are not redistributed)")

FF = ["MKT", "SMB", "HML", "UMD"]


@pytest.fixture(scope="module")
def tsmom():
    return data.aqr_original()["TSMOM"]


def test_original_file_covers_the_paper_window(tsmom):
    assert str(tsmom.index[0]) == paper.SAMPLE[0] and str(tsmom.index[-1]) == paper.SAMPLE[1]
    assert len(tsmom) == 300


def test_volatility_is_the_papers_12_percent(tsmom):
    assert abs(np.sqrt(12) * tsmom.std(ddof=1) - paper.FACTOR_VOL) < 0.005


def test_sharpe_ratio_above_one(tsmom):
    assert stats.sharpe(tsmom.to_numpy()) > 1.0


def test_table3_loadings(tsmom):
    fit = analysis.factor_regression(tsmom, data.factors(), FF).table()
    p = paper.TABLE3_MONTHLY
    for f in FF:
        assert abs(fit.loc[f, "coef"] - p["coef"][f]) < 0.05, f
        assert np.sign(fit.loc[f, "t"]) == np.sign(p["t"][f]) or abs(p["t"][f]) < 0.5
    assert fit.loc["UMD", "t"] > 5 and fit.loc["const", "t"] > 5
    # documented gap: the alpha on the authors' own file is lower than the printed 1.58%
    assert 0.010 < fit.loc["const", "coef"] < paper.TABLE3_MONTHLY["coef"]["const"]


def test_printed_alpha_is_not_consistent_with_the_file(tsmom):
    """Using the paper's own printed loadings, this series implies an alpha near 1.2%
    a month, well below the printed 1.58%; see README."""
    ff = data.factors().loc[tsmom.index]
    implied = tsmom.mean() - sum(paper.TABLE3_MONTHLY["coef"][f] * ff[f].mean() for f in FF)
    assert implied < paper.TABLE3_MONTHLY["coef"]["const"] - 0.003


def test_straddle_shape(tsmom):
    fit = analysis.straddle_regression(tsmom, data.factors()["MKT"])
    assert fit.coef[2] > 0 and fit.t[2] > 2.5
    assert abs(fit.t[1]) < 2
