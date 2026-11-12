import numpy as np
import pandas as pd
import pytest

from overcharge.data import load_jec
from overcharge.models import (
    DummyEstimate,
    circular_shift_test,
    drop_transition_weeks,
    fit_dummy,
    fit_forecast,
    leave_one_episode_out,
)

TRUE_B = 0.25


@pytest.fixture(scope="module")
def real():
    return load_jec()


@pytest.fixture(scope="module")
def simulated(real):
    """Real calendar and regimes, simulated prices with a known overcharge."""
    rng = np.random.default_rng(0)
    df = real[["week", "season", "lakes", "cartel", "episode"]].copy()
    seasonal = 0.05 * np.sin(2 * np.pi * df["season"] / 13)
    df["log_price"] = np.log(0.2) + seasonal - 0.1 * df["lakes"] + TRUE_B * df["cartel"] \
        + rng.normal(0, 0.03, len(df))
    df["price"] = np.exp(df["log_price"])
    return df


def test_dummy_recovers_known_overcharge(simulated):
    est = fit_dummy(simulated, "sim")
    low, high = est.ci()
    assert low < TRUE_B < high
    assert est.b == pytest.approx(TRUE_B, abs=0.02)


def test_forecast_recovers_known_overcharge(simulated):
    cartel = simulated[simulated["cartel"] == 1]
    war = simulated[simulated["cartel"] == 0]
    but_for = fit_forecast(war, cartel).but_for_price
    assert np.log(cartel["price"].sum() / but_for.sum()) == pytest.approx(TRUE_B, abs=0.02)


def test_forecast_never_uses_cartel_weeks(simulated):
    """Changing cartel week prices must not move the but for prices (no leakage)."""
    cartel = simulated[simulated["cartel"] == 1]
    war = simulated[simulated["cartel"] == 0]
    shocked = cartel.assign(log_price=cartel["log_price"] + 1, price=cartel["price"] * np.e)
    assert np.allclose(fit_forecast(war, cartel).but_for_price, fit_forecast(war, shocked).but_for_price)


def test_forecast_refuses_unseen_season(simulated):
    war = simulated[simulated["cartel"] == 0]
    with pytest.raises(ValueError):
        fit_forecast(war[war["season"] != 1], war[war["season"] == 1])


def test_kennedy_correction():
    est = DummyEstimate("x", b=0.4, se=0.1, n=100)
    assert est.overcharge_pct == pytest.approx(np.exp(0.4 - 0.005) - 1)


def test_drop_transition_weeks(real):
    """Each of the 21 later spells loses its first two weeks, or all of it if shorter."""
    spell_lengths = real.groupby("episode").size().iloc[1:]
    expected_drop = int(np.minimum(spell_lengths, 2).sum())
    assert len(drop_transition_weeks(real)) == len(real) - expected_drop


def test_permutation_finds_no_placebo_as_large_on_real_data(real):
    result = circular_shift_test(real, fit_dummy(real, "p").b)
    assert result.n_placebos == 277
    assert result.n_as_large == 0
    assert result.p_value == pytest.approx(1 / 278)


def test_permutation_is_not_significant_under_the_null(simulated):
    null = simulated.assign(log_price=simulated["log_price"] - TRUE_B * simulated["cartel"])
    result = circular_shift_test(null, fit_dummy(null, "null").b)
    assert result.p_value > 0.05


def test_validation_covers_every_war_week(real):
    v = leave_one_episode_out(real)
    assert v["weeks_scored"].sum() + v["weeks_skipped"].sum() == (real["cartel"] == 0).sum()


def test_cartel_raises_price(real):
    """Sign check: collusion should raise, not lower, the price."""
    assert fit_dummy(real, "sign").b > 0
