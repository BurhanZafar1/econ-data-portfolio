"""Known answers: output printed by the authors' did package on the same data.

Sources: the did package README (group time effects with est_method="reg") and
the "Getting Started" vignette (pre test, event study, balanced event study,
overall group effect).
"""

import numpy as np
import pytest

from staggered_did.aggregate import (
    event_study,
    group_att,
    simple_att,
    treated_states_by_event_time,
)
from staggered_did.group_time import (
    GroupTimeResult,
    estimate_group_time,
    outcome_regression_did,
)
from staggered_did.inference import standard_errors, wald_pretest
from staggered_did.panel import Panel

# Group, time, ATT(g, t), bootstrap standard error from the package README.
PUBLISHED_ATT = [
    (2004, 2004, -0.0105, 0.0246), (2004, 2005, -0.0704, 0.0332),
    (2004, 2006, -0.1373, 0.0397), (2004, 2007, -0.1008, 0.0357),
    (2006, 2004, 0.0065, 0.0229), (2006, 2005, -0.0028, 0.0197),
    (2006, 2006, -0.0046, 0.0179), (2006, 2007, -0.0412, 0.0192),
    (2007, 2004, 0.0305, 0.0154), (2007, 2005, -0.0027, 0.0164),
    (2007, 2006, -0.0311, 0.0184), (2007, 2007, -0.0261, 0.0170),
]
PUBLISHED_EVENT_STUDY = {
    -3: 0.0305, -2: -0.0006, -1: -0.0245, 0: -0.0199,
    1: -0.0510, 2: -0.1373, 3: -0.1008, "overall": -0.0772,
}


def test_group_time_effects_match_published_output(result: GroupTimeResult) -> None:
    table = result.table.set_index(["group", "time"])
    for group, time, att, _ in PUBLISHED_ATT:
        assert table.loc[(group, time), "att"] == pytest.approx(att, abs=5.1e-5)


def test_analytic_se_close_to_published_bootstrap(result: GroupTimeResult) -> None:
    published = np.array([row[3] for row in PUBLISHED_ATT])
    ours = standard_errors(result.influence)
    assert np.abs(ours / published - 1).max() < 0.10


def test_pretest_p_value_matches_published(result: GroupTimeResult) -> None:
    pre = ~result.table["post"].to_numpy()
    _, df, p_value = wald_pretest(result.table["att"].to_numpy()[pre], result.influence[:, pre])
    assert df == 5
    assert p_value == pytest.approx(0.16812, abs=5e-6)


def test_event_study_matches_published(result: GroupTimeResult) -> None:
    dynamic = event_study(result)
    assert dict(zip(dynamic.labels, np.round(dynamic.estimate, 4).tolist())) == pytest.approx(
        PUBLISHED_EVENT_STUDY, abs=1.1e-4
    )


def test_balanced_event_study_matches_published(result: GroupTimeResult) -> None:
    balanced = event_study(result, balance_e=1)
    assert balanced.labels == [-2, -1, 0, 1, "overall"]
    assert balanced.estimate[-1] == pytest.approx(-0.0288, abs=5.1e-5)
    assert balanced.estimate[2] == pytest.approx(-0.0066, abs=5.1e-5)


def test_overall_group_effect_matches_published(result: GroupTimeResult) -> None:
    assert group_att(result).estimate[-1] == pytest.approx(-0.031, abs=5.1e-4)


def test_simple_att_by_hand(result: GroupTimeResult) -> None:
    """Size weights 20, 40, 131 over 4, 2 and 1 post years."""
    table = result.table[result.table["post"]]
    sizes = table["group"].map({2004: 20, 2006: 40, 2007: 131}).to_numpy()
    by_hand = np.sum(sizes * table["att"].to_numpy()) / sizes.sum()
    assert simple_att(result).estimate[0] == pytest.approx(by_hand)


def test_att_by_hand_for_one_cell(panel: Panel) -> None:
    """ATT(2004, 2004): two differences of raw means."""
    change = panel.y[:, 1] - panel.y[:, 0]
    by_hand = change[panel.cohort == 2004].mean() - change[panel.cohort == 0].mean()
    table = estimate_group_time(panel).table.set_index(["group", "time"])
    assert table.loc[(2004, 2004), "att"] == pytest.approx(by_hand)


def test_influence_functions_average_to_zero(result: GroupTimeResult) -> None:
    assert np.abs(result.influence.mean(axis=0)).max() < 1e-10


def test_regression_adjustment_removes_a_covariate_trend() -> None:
    """Treated units have higher x; outcomes trend with x; true effect is 1."""
    x = np.arange(8.0)
    treated = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=bool)
    control = ~treated
    change = 2.0 * x + treated.astype(float)
    design = np.column_stack([np.ones(8), x])
    att, psi = outcome_regression_did(change, treated, control, design)
    assert att == pytest.approx(1.0)
    assert np.abs(psi).max() < 1e-9


def test_not_yet_controls_exclude_units_already_treated(panel: Panel) -> None:
    table = estimate_group_time(panel, control="notyet").table.set_index(["group", "time"])
    assert table.loc[(2004, 2005), "n_control"] == 309 + 40 + 131
    assert table.loc[(2004, 2006), "n_control"] == 309 + 131
    assert table.loc[(2004, 2007), "n_control"] == 309


def test_not_yet_controls_with_universal_base_are_clean_in_both_years(panel: Panel) -> None:
    """For cohort 2006 in 2003 the base is 2005, so 2004 adopters are excluded."""
    table = estimate_group_time(
        panel, control="notyet", base_period="universal"
    ).table.set_index(["group", "time"])
    assert table.loc[(2006, 2003), "n_control"] == 309 + 131


def test_universal_base_keeps_post_effects_and_omits_reference_year(panel: Panel) -> None:
    varying = estimate_group_time(panel).table
    universal = estimate_group_time(panel, base_period="universal").table
    keep = ["group", "time", "att"]
    merged = varying[varying["post"]][keep].merge(
        universal[universal["post"]][keep], on=["group", "time"]
    )
    assert merged["att_x"].to_numpy() == pytest.approx(merged["att_y"].to_numpy())
    assert not ((universal["time"] - universal["group"]) == -1).any()


def test_years_two_and_three_rest_on_one_state(result: GroupTimeResult) -> None:
    states = treated_states_by_event_time(result)
    assert states[2] == 1 and states[3] == 1
    assert states[0] == 13
