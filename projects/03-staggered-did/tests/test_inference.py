"""Standard errors, joint bands, placebo logic and the simulated check."""

import numpy as np
import pandas as pd
import pytest

from staggered_did.aggregate import Aggregate, group_att, weight_influence
from staggered_did.group_time import GroupTimeResult
from staggered_did.inference import (
    covariance,
    standard_errors,
    sup_t_critical_value,
    wald_pretest,
)
from staggered_did.panel import Panel
from staggered_did.placebo import leave_one_state_out, randomization_test, state_placebo_test
from staggered_did.simulate import STRESS_TEST, monte_carlo


def test_se_of_a_sample_mean_by_hand() -> None:
    sample = np.array([1.0, 2.0, 3.0, 4.0])
    influence = (sample - sample.mean())[:, None]
    expected = np.sqrt(np.mean((sample - sample.mean()) ** 2) / 4)
    assert standard_errors(influence)[0] == pytest.approx(expected)


def test_cluster_covariance_by_hand() -> None:
    influence = np.array([[1.0], [1.0], [-1.0], [-1.0]])
    clusters = np.array([1, 1, 2, 2])
    expected = (2 / 1) * (2.0**2 + 2.0**2) / 4**2
    assert covariance(influence, clusters)[0, 0] == pytest.approx(expected)


def test_wald_by_hand() -> None:
    influence = np.array([[1.0], [-1.0], [1.0], [-1.0]])
    statistic, df, _ = wald_pretest(np.array([0.5]), influence)
    assert statistic == pytest.approx(0.5**2 / (4 / 16))
    assert df == 1


def test_joint_band_is_wider_than_pointwise(result: GroupTimeResult, panel: Panel) -> None:
    critical = sup_t_critical_value(result.influence, panel.units, seed=1)
    assert critical > 1.96


def test_weight_influence_has_mean_zero(result: GroupTimeResult) -> None:
    columns = weight_influence(result, result.panel.groups)
    assert np.abs(columns.mean(axis=0)).max() < 1e-12


def test_aggregate_estimate_is_a_weighted_mean(result: GroupTimeResult) -> None:
    aggregate: Aggregate = group_att(result)
    low, high = aggregate.estimate[:-1].min(), aggregate.estimate[:-1].max()
    assert low <= aggregate.estimate[-1] <= high


def test_placebo_counts_and_p_value(panel: Panel) -> None:
    table = state_placebo_test(panel, 2004, 17).set_index("year")
    assert table["n_placebos"].unique().tolist() == [16]
    row = table.loc["average"]
    assert row["p_value"] == pytest.approx((1 + row["n_as_extreme"]) / 17)


def test_placebo_actual_equals_group_time_effect(panel: Panel, result: GroupTimeResult) -> None:
    actual = state_placebo_test(panel, 2004, 17).set_index("year")["actual"]
    cells = result.table[result.table["group"] == 2004].set_index("time")["att"]
    assert actual.loc[2006] == pytest.approx(cells.loc[2006])


def test_simulation_shows_twfe_bias_and_recovers_truth() -> None:
    row: pd.Series = monte_carlo(STRESS_TEST, draws=100, n_units=500, seed=5).iloc[0]
    assert row["mean_twfe"] < 0.5 * row["mean_truth"]
    assert row["mean_group_time"] == pytest.approx(row["mean_truth"], abs=0.01)


def test_randomization_test_reports_the_actual_estimate(panel: Panel) -> None:
    row = randomization_test(panel, draws=20, seed=3).iloc[0]
    assert row["estimate"] == pytest.approx(-0.0310, abs=5.1e-5)
    assert 0 < row["p_value_estimate"] <= 1


def test_leave_one_out_covers_each_treated_state(panel: Panel) -> None:
    table = leave_one_state_out(panel)
    assert len(table) == 13
    assert 17 in table["dropped_state_fips"].tolist()
