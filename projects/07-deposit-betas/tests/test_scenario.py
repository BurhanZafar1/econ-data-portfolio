"""Hand calculations for the scenario projection."""

import numpy as np
import pytest

from deposit_beta.regression import PassThrough
from deposit_beta.scenario import Scenario, project_rate


def make_fit(up, down):
    return PassThrough("savings", "toy", len(up) - 1, 0, 0.0, sum(up), 0, sum(down), 0, 0, 0, 1, 0, 0,
                       tuple(up), tuple(down))


def test_single_hike_passes_through_with_lags():
    fit = make_fit([0.2, 0.1], [0.05, 0.05])
    path = project_rate(1.0, np.array([0.0]), np.array([1.0, 0.0, 0.0]), fit)
    np.testing.assert_allclose(path, [1.2, 1.3, 1.3])


def test_history_keeps_passing_through():
    fit = make_fit([0.2, 0.1], [0.05, 0.05])
    path = project_rate(1.0, np.array([1.0]), np.zeros(2), fit)  # last month's hike, lag 1 still due
    np.testing.assert_allclose(path, [1.1, 1.1])


def test_rates_floor_at_zero():
    fit = make_fit([0.0], [0.5])
    path = project_rate(0.1, np.array([]), np.array([-1.0]), fit)
    assert path[0] == pytest.approx(0.0)


def test_scenario_path():
    assert Scenario("x", {2: -0.25}).path(3).tolist() == [0.0, -0.25, 0.0]
    with pytest.raises(ValueError):
        Scenario("x", {13: 0.25}).path(12)
