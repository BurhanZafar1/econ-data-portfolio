"""Hand calculated checks for diversion ratios and upward pricing pressure."""

import pytest

from merger_screen.diversion import breakeven_margin, guppi, net_upp_per_dollar, proportional_diversion


def test_proportional_diversion_hand_calc():
    # Firm 1 has 40 percent; firm 2 has 30 of the remaining 60 percent, so D12 = 0.5.
    assert proportional_diversion(40, 30) == pytest.approx(0.5)
    assert proportional_diversion(40, 30, aggregate_diversion=0.6) == pytest.approx(0.3)


def test_diversion_to_all_rivals_sums_to_aggregate():
    shares = [40, 30, 20, 10]
    total = sum(proportional_diversion(shares[0], s) for s in shares[1:])
    assert total == pytest.approx(1.0)


def test_guppi_hand_calc():
    # D12 = 0.2, margin 0.5, P2 / P1 = 1.2 gives 0.2 * 0.5 * 1.2 = 0.12.
    assert guppi(0.2, 0.5, 1.2) == pytest.approx(0.12)


def test_net_upp_matches_farrell_shapiro_inequality():
    # Direct form: D12 (P2 - C2) - E C1 with P1 = 10, C1 = 6, P2 = 12, C2 = 6, E = 0.1.
    d12, p1, c1, p2, c2, e = 0.25, 10.0, 6.0, 12.0, 6.0, 0.1
    direct = d12 * (p2 - c2) - e * c1
    per_dollar = net_upp_per_dollar(d12, 1 - c1 / p1, 1 - c2 / p2, e, p2 / p1)
    assert per_dollar * p1 == pytest.approx(direct)


def test_breakeven_margin_zeroes_net_upp():
    m = breakeven_margin(0.2, 0.1)
    assert m == pytest.approx(1 / 3)
    assert net_upp_per_dollar(0.2, m, m, 0.1) == pytest.approx(0.0)


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        proportional_diversion(100, 0)
    with pytest.raises(ValueError):
        proportional_diversion(20, 10, aggregate_diversion=1.5)
