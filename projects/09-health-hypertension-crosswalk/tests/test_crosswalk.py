import numpy as np
import pandas as pd
import pytest

from htn_crosswalk.crosswalk import (
    Spec, adjust_draws, design_matrix, fit_crosswalk, rogan_gladen, summarise_draws,
)
from htn_crosswalk.extract import XW_LABELS
from htn_crosswalk.paired import expit, logit

TRUE_D = dict(zip(XW_LABELS, [-0.8, -0.2, 0.0, 0.15, 0.3]))


def _paired(cycles=("2011-2012", "2013-2014", "2015-2016"), noise=0.0, seed=1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = [
        {"cycle": c, "xw_group": g, "d": d + noise * rng.normal(), "se_d": 0.05}
        for c in cycles for g, d in TRUE_D.items()
    ]
    return pd.DataFrame(rows)


def test_rogan_gladen_hand_calculation():
    # (0.30 + 0.90 - 1) / (0.80 + 0.90 - 1) = 0.20 / 0.70
    assert rogan_gladen(np.array([0.30]), np.array([0.80]), np.array([0.90]))[0] == pytest.approx(0.2 / 0.7)
    assert rogan_gladen(np.array([0.05]), np.array([0.8]), np.array([0.9]))[0] == 0.0


def test_fit_recovers_known_crosswalk():
    xw = fit_crosswalk(_paired(), Spec(by_sex=False, trend=False))
    np.testing.assert_allclose(xw.model.beta, list(TRUE_D.values()), atol=1e-12)
    assert xw.model.tau2 == 0.0


def test_window_uses_only_latest_cycles():
    paired = pd.concat([_paired(("2001-2002",)).assign(d=5.0), _paired()])
    xw = fit_crosswalk(paired, Spec(by_sex=False, trend=False, window=3))
    assert xw.cycles == ("2011-2012", "2013-2014", "2015-2016")
    np.testing.assert_allclose(xw.model.beta, list(TRUE_D.values()), atol=1e-12)


def test_adjustment_round_trip_and_reproducible_draws():
    xw = fit_crosswalk(_paired(), Spec(by_sex=False, trend=False))
    cells = pd.DataFrame({"xw_group": list(XW_LABELS), "mid_year": 2015.5})
    p_self = np.array([0.10, 0.20, 0.30, 0.45, 0.60])
    draws = adjust_draws(p_self, np.full(5, 1e-9), cells, xw, np.random.default_rng(7))
    expected = expit(logit(p_self) + np.array(list(TRUE_D.values())))
    np.testing.assert_allclose(summarise_draws(draws)["mean"], expected, atol=2e-3)
    again = adjust_draws(p_self, np.full(5, 1e-9), cells, xw, np.random.default_rng(7))
    np.testing.assert_array_equal(draws, again)


def test_interval_widens_with_heterogeneity():
    cells = pd.DataFrame({"xw_group": list(XW_LABELS), "mid_year": 2015.5})
    tight = fit_crosswalk(_paired(), Spec(False, False))
    loose = fit_crosswalk(_paired(noise=0.3), Spec(False, False))
    assert loose.model.tau2 > 0
    assert (loose.predict(cells)[1] > tight.predict(cells)[1]).all()


def test_design_matrix_shapes():
    cells = pd.DataFrame({"xw_group": ["18-34", "65+"], "sex": ["Male", "Female"], "mid_year": [2010.0, 2020.0]})
    x, names = design_matrix(cells, Spec(by_sex=True, trend=True))
    assert x.shape == (2, 15) and len(names) == 15
    assert x[1, names.index("65+ trend per decade")] == pytest.approx(1.0)
    assert x[0, names.index("18-34 Male")] == 1.0
