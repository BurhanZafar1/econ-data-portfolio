"""Hand calculations for cycle betas and checks on the shipped FRED data."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from deposit_beta.cycles import CYCLES, beta_path, cycle_beta, cycle_table, last_move_month
from deposit_beta.data import ERA_2009, ERA_2021, PRODUCTS, add_changes, build_monthly_panel, to_monthly_mean

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


@pytest.fixture(scope="module")
def panel():
    return build_monthly_panel(RAW)


def test_cycle_beta_hand_calculation():
    # Deposit rate 0.10 -> 0.60 while the funds rate goes 0.25 -> 2.75: 0.5 / 2.5 = 0.2.
    assert cycle_beta(0.10, 0.60, 0.25, 2.75) == pytest.approx(0.2)
    with pytest.raises(ValueError):
        cycle_beta(0.1, 0.2, 1.0, 1.0)


def test_2022_cd_cycle_beta_by_hand(panel):
    # FRED values: FEDFUNDS 0.08 (2022-02) and 5.33 (2024-08); NDR12MCD 0.14 and 1.85.
    table = cycle_table(panel, PRODUCTS)
    row = table[(table["cycle"] == "2022-2023 hikes") & (table["product"] == "cd_12m")].iloc[0]
    assert (row.ff_base, row.ff_end) == pytest.approx((0.08, 5.33))
    assert (row.deposit_base, row.deposit_end) == pytest.approx((0.14, 1.85))
    assert row.beta == pytest.approx((1.85 - 0.14) / (5.33 - 0.08))


def test_effective_rate_inside_published_target_range(panel):
    # FOMC set the target range to 5.25-5.50 percent on 26 July 2023.
    assert 5.25 <= panel.loc[pd.Period("2023-08", "M"), "fedfunds"] <= 5.50


def test_monthly_mean_drops_partial_months():
    weeks = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=pd.to_datetime(
        ["2020-01-06", "2020-01-13", "2020-01-20", "2020-02-03", "2020-02-10"]))
    monthly = to_monthly_mean(weeks, min_obs=3)
    assert list(monthly.index.astype(str)) == ["2020-01"]
    assert monthly.iloc[0] == pytest.approx(2.0)


def test_panel_structure(panel):
    assert str(panel.index[0]) == "2009-06" and str(panel.index[-1]) == "2026-10"
    assert len(panel) == 209
    assert set(panel["era"]) == {ERA_2009, ERA_2021}
    assert str(panel.index[panel["era"] == ERA_2021][0]) == "2021-04"
    assert (panel[list(PRODUCTS)] >= 0).all().all()


def test_change_across_method_break_is_blank(panel):
    changes = add_changes(panel)
    at_break = changes.loc[pd.Period("2021-04", "M")]
    assert all(np.isnan(at_break[f"d_{p}"]) for p in PRODUCTS)
    assert at_break["d_fedfunds"] == pytest.approx(0.0)


def test_cycle_windows_stay_in_one_era(panel):
    for cycle in CYCLES:
        assert panel.loc[pd.Period(cycle.base, "M"), "era"] == panel.loc[pd.Period(cycle.end, "M"), "era"]


def test_beta_path_masks_small_moves():
    idx = pd.period_range("2020-01", periods=3, freq="M")
    toy = pd.DataFrame({"fedfunds": [1.0, 1.1, 2.0], "savings": [0.1, 0.2, 0.3]}, index=idx)
    path = beta_path(toy, "savings", "2020-01", "2020-03")
    assert np.isnan(path.iloc[1])
    assert path.iloc[2] == pytest.approx(0.2)


def test_last_move_month_finds_end_of_moves(panel):
    # The 2022-2023 hikes ended with the July 2023 move; August 2023 is the first full month at 5.33.
    assert last_move_month(panel, "2022-02", "2024-08") == "2023-08"
    toy = pd.DataFrame({"fedfunds": [1.0, 1.5, 2.0, 2.0, 2.02]}, index=pd.period_range("2020-01", periods=5, freq="M"))
    assert last_move_month(toy, "2020-01", "2020-05") == "2020-03"
