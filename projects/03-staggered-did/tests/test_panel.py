"""Input checks and basic facts about the sample."""

import numpy as np
import pandas as pd
import pytest

from staggered_did.panel import Panel, build_panel, drop_cohort


def test_sample_matches_documented_structure(panel: Panel) -> None:
    assert panel.y.shape == (500, 5)
    cohorts, counts = np.unique(panel.cohort, return_counts=True)
    assert cohorts.tolist() == [0, 2004, 2006, 2007]
    assert counts.tolist() == [309, 20, 40, 131]
    assert np.unique(panel.clusters).size == 29


def test_treatment_was_assigned_by_state(panel: Panel) -> None:
    for state in np.unique(panel.clusters):
        assert np.unique(panel.cohort[panel.clusters == state]).size == 1


def test_illinois_is_the_only_2004_state(panel: Panel) -> None:
    assert np.unique(panel.clusters[panel.cohort == 2004]).tolist() == [17]


def test_unbalanced_panel_is_refused() -> None:
    frame = pd.DataFrame({
        "unit": [1, 1, 2], "year": [1, 2, 1], "y": [0.0, 1.0, 2.0],
        "cohort": [0, 0, 0], "cluster": [1, 1, 2],
    })
    with pytest.raises(ValueError, match="balanced"):
        build_panel(frame, "unit", "year", "y", "cohort", "cluster")


def test_drop_cohort_removes_only_that_cohort(panel: Panel) -> None:
    smaller = drop_cohort(panel, 2004)
    assert smaller.n_units == 480
    assert 2004 not in smaller.cohort
