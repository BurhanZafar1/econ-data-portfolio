import numpy as np
import pandas as pd
import pytest

from overcharge.damages import damages_from_log_overcharge, overcharge_damages, volume_effect


@pytest.fixture
def weeks():
    price = pd.Series([0.30, 0.25])
    quantity = pd.Series([1000.0, 2000.0])
    return pd.DataFrame({"price": price, "quantity": quantity, "revenue": price * quantity * 20})


def test_hand_calculated_damages(weeks):
    """(0.30 - 0.20) * 1000 * 20 + (0.25 - 0.20) * 2000 * 20 = 2000 + 2000."""
    assert overcharge_damages(weeks, pd.Series([0.20, 0.20])) == pytest.approx(4000.0)


def test_two_damage_formulas_agree(weeks):
    b = 0.3
    but_for = weeks["price"] * np.exp(-b)
    assert damages_from_log_overcharge(weeks, b) == pytest.approx(overcharge_damages(weeks, but_for))


def test_damages_plus_but_for_revenue_equal_actual_revenue(weeks):
    b = 0.25
    but_for_revenue = (weeks["price"] * np.exp(-b) * weeks["quantity"] * 20).sum()
    assert damages_from_log_overcharge(weeks, b) + but_for_revenue == pytest.approx(weeks["revenue"].sum())


def test_zero_overcharge_means_zero_damages(weeks):
    assert damages_from_log_overcharge(weeks, 0.0) == 0.0


def test_volume_effect_signs(weeks):
    none = volume_effect(weeks, 0.3, elasticity=0.0)
    assert none.lost_tons == pytest.approx(0.0) and none.deadweight_loss == pytest.approx(0.0)
    some = volume_effect(weeks, 0.3, elasticity=-1.0)
    assert some.lost_tons > 0 and some.deadweight_loss > 0
    # Unit elasticity: Q_but_for = Q * exp(0.3).
    assert some.lost_pct == pytest.approx(np.exp(0.3) - 1)
