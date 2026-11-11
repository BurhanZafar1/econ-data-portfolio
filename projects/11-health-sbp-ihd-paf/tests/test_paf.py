"""Known answer tests for the PAF formulas."""

import numpy as np
import pytest
from scipy import stats

from sbp_paf.paf import levin_paf, normal_paf_closed_form, relative_risk, weighted_paf
from sbp_paf.risks import ettehad_cells, log_se_from_ci, log_slope_from_hr


def test_hand_calculated_two_point_paf():
    # Half the population at the TMREL (RR 1), half 20 mmHg above with HR 0.5 per 20 lower (RR 2).
    # Mean RR = 1.5, so PAF = (1.5 - 1) / 1.5 = 1/3 exactly.
    beta = log_slope_from_hr(0.5)
    sbp = np.array([115.0, 135.0])
    assert weighted_paf(sbp, np.array([1.0, 1.0]), beta, 115.0) == pytest.approx(1 / 3, abs=1e-12)


def test_matches_levin_formula_for_binary_exposure():
    # 30% exposed at 40 mmHg above the TMREL with HR 0.6 per 20 lower: RR = (1/0.6)^2.
    beta = log_slope_from_hr(0.6)
    rr = float(relative_risk(150.0, beta, 110.0))
    assert rr == pytest.approx((1 / 0.6) ** 2)
    sbp = np.array([105.0, 150.0])  # the unexposed are below the TMREL, so RR = 1
    weights = np.array([0.7, 0.3])
    assert weighted_paf(sbp, weights, beta, 110.0) == pytest.approx(levin_paf(0.3, rr), abs=1e-12)


def test_numerical_integration_matches_normal_closed_form():
    # With the TMREL far below the distribution, truncation never binds and E[RR] is lognormal.
    mu, sigma, beta, tmrel = 130.0, 18.0, log_slope_from_hr(0.54), 40.0
    grid = np.linspace(mu - 10 * sigma, mu + 10 * sigma, 200_001)
    weights = stats.norm.pdf(grid, mu, sigma)
    numeric = weighted_paf(grid, weights, beta, tmrel)
    assert numeric == pytest.approx(normal_paf_closed_form(mu, sigma, beta, tmrel), rel=1e-9)


def test_no_exposure_above_tmrel_gives_zero_paf():
    sbp = np.array([100.0, 105.0, 109.9])
    assert weighted_paf(sbp, np.ones(3), 0.05, 110.0) == 0.0


def test_draw_vectorisation_matches_loop():
    rng = np.random.default_rng(1)
    sbp = rng.normal(130, 15, 200)
    weights = rng.uniform(1, 3, (200, 5))
    betas, tmrels = rng.uniform(0.02, 0.04, 5), rng.uniform(110, 115, 5)
    vec = weighted_paf(sbp, weights, betas, tmrels)
    loop = [weighted_paf(sbp, weights[:, d], betas[d], tmrels[d]) for d in range(5)]
    np.testing.assert_allclose(vec, loop, rtol=1e-12)


def test_relative_risk_conversions():
    # PSC 60-69 both sexes: HR 0.54 (0.53 to 0.55) per 20 mmHg lower.
    assert np.exp(20 * log_slope_from_hr(0.54)) == pytest.approx(1 / 0.54)
    assert log_se_from_ci(0.53, 0.55) == pytest.approx((np.log(0.55) - np.log(0.53)) / 3.919927969, rel=1e-9)
    # Ettehad 2016: RR 0.83 per 10 mmHg, so 0.83^2 per 20 mmHg.
    cells = ettehad_cells()
    assert len(cells) == 10
    assert np.exp(-10 * cells["beta"].iloc[0]) == pytest.approx(0.83)


def test_share_attributable_below_threshold():
    import pandas as pd

    from sbp_paf.estimates import share_attributable_below

    # One cell: people at the TMREL contribute nothing; one at 132.5 and one at 152.5 mmHg.
    # With HR 0.5 per 20 lower and TMREL 112.5, RR = 2 and 4, so excess risks are 1 and 3.
    extract = pd.DataFrame({"sex": "Male", "age_group": "50-59", "sbp": [112.5, 132.5, 152.5],
                            "wt_mec": [1.0, 1.0, 1.0]})
    cells = pd.DataFrame({"sex": ["Male"], "age_group": ["50-59"], "beta": [log_slope_from_hr(0.5)]})
    deaths = pd.DataFrame({"sex": ["Male"], "age_group": ["50-59"], "deaths": [700]})
    assert share_attributable_below(extract, cells, deaths, 140.0) == pytest.approx(0.25)
    assert share_attributable_below(extract, cells, deaths, 120.0) == pytest.approx(0.0)


def test_aggregation_weights_cell_pafs_by_deaths():
    import pandas as pd

    from sbp_paf.estimates import attributable

    # Two cells with constant draws: PAF 0.5 on 100 deaths and 0.2 on 300 deaths.
    # Overall PAF = (50 + 60) / 400 = 0.275; attributable deaths = 110.
    cells = pd.DataFrame({"sex": ["Male", "Female"], "age_group": ["40-49", "40-49"], "n": [10, 10],
                          "central": [0.5, 0.2], "draws": [np.full(4, 0.5), np.full(4, 0.2)]})
    deaths = pd.DataFrame({"sex": ["Male", "Female"], "age_group": ["40-49", "40-49"], "deaths": [100, 300]})
    out = attributable(cells, deaths)
    both = out[out["sex"] == "Both"].iloc[0]
    assert both["paf_mean"] == pytest.approx(0.275)
    assert both["paf_central"] == pytest.approx(0.275)
    assert both["attrib_deaths_mean"] == pytest.approx(110.0)


def test_cells_sharing_a_source_share_a_draw():
    import pandas as pd

    from sbp_paf.estimates import DrawInputs, cell_draws
    from sbp_paf.risks import ettehad_cells

    # Identical people in every cell plus one shared source must give identical draws in every cell.
    rng = np.random.default_rng(2)
    rows = [{"sex": s, "age_group": a, "sbp": v, "wt_mec": 1.0}
            for s in ("Male", "Female") for a in ("40-49", "50-59", "60-69", "70-79", "80+") for v in (120.0, 140.0)]
    extract = pd.DataFrame(rows)
    inputs = DrawInputs(rep_weights=np.ones((len(extract), 50)), beta_z=rng.standard_normal((10, 50)),
                        tmrel=np.full(50, 112.5))
    out = cell_draws(extract, ettehad_cells(), inputs)
    first = out["draws"].iloc[0]
    for d in out["draws"]:
        np.testing.assert_allclose(d, first)
