"""Known answer tests for the standard populations."""

import math

import pandas as pd
import pytest

from nhanes_bp.standards import (
    NCHS_GROUPS,
    US_2000_ADULT,
    WHO_2000_2025,
    WHO_ADULT_GROUPS,
    aggregate_weights,
    assign_age_group,
)


def test_who_standard_table_adds_to_100_within_published_rounding():
    # Ahmad et al. (2001) Table 4 lists 21 rounded percents; they add to 100.035.
    assert len(WHO_2000_2025) == 21
    assert sum(WHO_2000_2025.values()) == pytest.approx(100.035, abs=1e-9)


def test_who_adult_weights_sum_to_one_and_match_hand_calculation():
    w = aggregate_weights(WHO_2000_2025, WHO_ADULT_GROUPS)
    adult_total = 100.035 - (8.86 + 8.69 + 8.60 + 8.47)
    assert math.isclose(w.sum(), 1.0)
    assert w["20-29"] == pytest.approx((8.22 + 7.93) / adult_total)
    assert w["80+"] == pytest.approx((0.91 + 0.44 + 0.15 + 0.04 + 0.005) / adult_total)
    assert list(w) == sorted(w, reverse=True)  # the standard thins out with age


def test_us_2000_adult_total_matches_klein_schoenborn_distribution_8():
    # The Table 1 adult rows must add to the 18+ total printed in Table 2, Distribution #8.
    assert sum(US_2000_ADULT.values()) == 203_851


def test_nchs_three_group_weights():
    w = aggregate_weights(US_2000_ADULT, NCHS_GROUPS)
    assert w["18-39"] == pytest.approx(85_671 / 203_851)
    assert w["40-59"] == pytest.approx(72_816 / 203_851)
    assert w["60+"] == pytest.approx(45_364 / 203_851)
    assert round(w["18-39"], 6) == 0.420263


def test_band_straddling_a_group_boundary_is_rejected():
    with pytest.raises(ValueError):
        aggregate_weights(WHO_2000_2025, [(18, 39)])  # would split the 15-19 band


def test_assign_age_group_top_codes_and_out_of_range():
    ages = pd.Series([18, 20, 29, 30, 80, 85])
    labels = assign_age_group(ages, WHO_ADULT_GROUPS).tolist()
    assert labels == ["", "20-29", "20-29", "30-39", "80+", "80+"]
