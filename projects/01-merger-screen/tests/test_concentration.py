"""Known answer tests for HHI and the 2023 Merger Guidelines presumption."""

import pytest

from merger_screen.concentration import (
    delta_hhi,
    delta_hhi_rounding_range,
    hhi,
    hhi_bounds,
    structural_presumption,
)


def test_guidelines_footnote_13_equal_firm_markets():
    # 2023 Merger Guidelines, footnote 13: five equal firms give 2,000; six give 1,667.
    assert hhi([20] * 5) == pytest.approx(2000)
    assert hhi([100 / 6] * 6) == pytest.approx(1667, abs=0.5)


def test_guidelines_footnote_14_change_is_2ab():
    # 2023 Merger Guidelines, footnote 14: shares of 20 and 5 percent raise the HHI by 200.
    assert delta_hhi(20, 5) == pytest.approx(200)


def test_delta_equals_post_minus_pre():
    shares = [40, 25, 20, 15]
    post = [40 + 15, 25, 20]
    assert hhi(post) - hhi(shares) == pytest.approx(delta_hhi(40, 15))


def test_heinz_footnote_9_worked_example():
    # FTC v. H.J. Heinz, 246 F.3d at 716 n.9: HHI of 1304; merging 13 and 5 adds 130.
    shares = [20, 17, 13, 12, 10, 10, 8, 5, 3, 2]
    assert hhi(shares) == pytest.approx(1304)
    assert delta_hhi(13, 5) == pytest.approx(130)


def test_monopoly_is_10000():
    assert hhi([100]) == 10000


def test_bounds_bracket_fringe():
    low, high = hhi_bounds([60, 30])
    assert low == pytest.approx(4500)
    assert high == pytest.approx(4500 + 10**2)
    assert hhi_bounds([50, 50]) == (5000, 5000)


@pytest.mark.parametrize(
    ("post", "change", "share", "hhi_test", "share_test"),
    [
        (1801, 101, 10, True, False),
        (1800, 500, 10, False, False),  # 1,800 exactly is not "greater than"
        (5000, 100, 40, False, False),  # 100 exactly is not "more than 100"
        (1500, 150, 31, False, True),   # share test can bite below 1,800
        (1500, 150, 30, False, False),
    ],
)
def test_presumption_uses_strict_thresholds(post, change, share, hhi_test, share_test):
    result = structural_presumption(post, change, share)
    assert result.hhi_test is hhi_test
    assert result.share_test is share_test
    assert result.presumed_illegal is (hhi_test or share_test)


def test_rounding_range_brackets_taxhawk_case():
    # 15.6 and 3.2 printed to one decimal: true change lies between 2(15.55)(3.15) and 2(15.65)(3.25).
    low, high = delta_hhi_rounding_range(15.6, 3.2)
    assert low == pytest.approx(97.965)
    assert high == pytest.approx(101.725)
    assert low < delta_hhi(15.6, 3.2) < high
