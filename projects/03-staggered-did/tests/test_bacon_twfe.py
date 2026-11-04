"""Goodman-Bacon decomposition and TWFE checks."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from staggered_did import bacon
from staggered_did.panel import Panel, build_panel
from staggered_did.twfe import _clustered_se, event_study_twfe, static_twfe, two_way_demean

DATA = Path(__file__).resolve().parents[1] / "data"


def math_reform_panel() -> Panel:
    frame = pd.read_csv(DATA / "math_reform.csv")
    frame["cohort"] = frame["reformyr_math"].fillna(0).astype(int)
    return build_panel(frame, "state", "class", "incearn_ln", "cohort", "state")


def test_summary_matches_bacondecomp_readme() -> None:
    """Published weights and means from the bacondecomp package README."""
    summary = bacon.summarize(bacon.decompose(math_reform_panel())).set_index("type")
    expected = {
        bacon.EARLY_VS_LATE: (0.06353, 0.02868),
        bacon.LATE_VS_EARLY: (0.05265, 0.03375),
        bacon.TREATED_VS_UNTREATED: (0.88382, -0.00129),
    }
    for kind, (weight, estimate) in expected.items():
        assert summary.loc[kind, "weight"] == pytest.approx(weight, abs=6e-6)
        assert summary.loc[kind, "avg_estimate"] == pytest.approx(estimate, abs=6e-6)


def test_one_cell_matches_bacondecomp_readme() -> None:
    table = bacon.decompose(math_reform_panel())
    row = table[(table["treated"] == 1987) & (table["control"] == "1985")].iloc[0]
    assert row["estimate"] == pytest.approx(0.04575585, abs=1e-7)
    assert row["weight"] == pytest.approx(0.031655309, abs=1e-8)


@pytest.mark.parametrize("build", ["mpdta", "math"])
def test_components_rebuild_twfe_exactly(panel: Panel, build: str) -> None:
    """Theorem 1: weights sum to one and the weighted sum equals TWFE."""
    data = panel if build == "mpdta" else math_reform_panel()
    table = bacon.decompose(data)
    assert table["weight"].sum() == pytest.approx(1.0)
    assert (table["weight"] * table["estimate"]).sum() == pytest.approx(
        static_twfe(data).coef[0], abs=1e-10
    )


def test_two_by_two_by_hand() -> None:
    """One switcher and one control over two periods: the textbook DiD."""
    panel = Panel(
        y=np.array([[1.0, 4.0], [2.0, 3.0]]),
        years=np.array([1, 2]),
        cohort=np.array([2, 0]),
        units=np.array([1, 2]),
        clusters=np.array([1, 2]),
    )
    assert bacon.decompose(panel)["estimate"].iloc[0] == pytest.approx(2.0)
    assert static_twfe(panel).coef[0] == pytest.approx(2.0)


def test_twfe_equals_dummy_variable_regression(panel: Panel) -> None:
    n, t = panel.y.shape
    units = np.repeat(np.eye(n), t, axis=0)
    years = np.tile(np.eye(t)[:, 1:], (n, 1))
    x = np.column_stack([panel.treated.ravel(), units, years])
    coef, *_ = np.linalg.lstsq(x, panel.y.ravel(), rcond=None)
    assert static_twfe(panel).coef[0] == pytest.approx(coef[0], abs=1e-10)


def test_twfe_matches_published_coefficient_sign_and_size(panel: Panel) -> None:
    fit = static_twfe(panel)
    assert fit.coef[0] == pytest.approx(-0.0365, abs=5.1e-5)
    # Treatment varies by state, so county clustering is too narrow here.
    assert fit.se_cluster[0] > fit.se_unit[0]


def test_cohort_weighted_long_difference_by_hand(panel: Panel) -> None:
    table = bacon.decompose(panel)
    rows = table[table["type"] == bacon.TREATED_VS_UNTREATED].set_index("treated")["estimate"]
    by_hand = (20 * rows[2004] + 40 * rows[2006] + 131 * rows[2007]) / 191
    assert bacon.cohort_weighted_long_difference(table, panel) == pytest.approx(by_hand)


def test_two_way_demean_leaves_zero_margins() -> None:
    matrix = np.arange(12.0).reshape(3, 4) ** 2
    out = two_way_demean(matrix)
    assert np.abs(out.mean(axis=0)).max() < 1e-12
    assert np.abs(out.mean(axis=1)).max() < 1e-12


def test_clustered_se_by_hand() -> None:
    """One regressor, two clusters: compute the sandwich on paper."""
    x = np.array([[1.0], [1.0], [1.0], [1.0]])
    resid = np.array([1.0, 1.0, -1.0, -1.0])
    ids = np.array([1, 1, 2, 2])
    scores_squared = 2.0**2 + 2.0**2
    correction = (2 / 1) * (3 / 3)
    expected = np.sqrt(scores_squared * correction) / 4.0
    assert _clustered_se(x, resid, ids, 1)[0] == pytest.approx(expected)


def test_event_study_omits_reference_year(panel: Panel) -> None:
    table = event_study_twfe(panel)
    assert -1 not in table["event_time"].tolist()
    assert table["event_time"].tolist() == [-4, -3, -2, 0, 1, 2, 3]
