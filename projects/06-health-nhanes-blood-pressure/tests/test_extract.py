"""Blood pressure averaging rules."""

import numpy as np
import pandas as pd
import pytest

from nhanes_bp.extract import average_readings


def frame(rows):
    return pd.DataFrame(rows, dtype=float)


def test_average_of_first_three_available_readings():
    sbp = frame([[120, 130, 140, np.nan], [np.nan, 110, 120, 130], [150, np.nan, np.nan, np.nan]])
    dbp = frame([[70, 80, 90, np.nan], [np.nan, 60, 70, 80], [95, np.nan, np.nan, np.nan]])
    out = average_readings(sbp, dbp)
    assert out["sbp"].tolist() == [130, 120, 150]
    assert out["n_readings"].tolist() == [3, 3, 1]
    assert out["dbp"].tolist() == [80, 70, 95]


def test_zero_diastolic_dropped_unless_all_zero():
    sbp = frame([[120, 120, 120, np.nan], [120, 120, np.nan, np.nan]])
    dbp = frame([[0, 60, 70, np.nan], [0, 0, np.nan, np.nan]])
    out = average_readings(sbp, dbp)
    assert out["dbp"].tolist() == [pytest.approx(65.0), 0.0]


def test_no_readings_gives_missing():
    nan_row = frame([[np.nan] * 4])
    out = average_readings(nan_row, nan_row)
    assert np.isnan(out["sbp"].iloc[0]) and np.isnan(out["dbp"].iloc[0])
    assert out["n_readings"].iloc[0] == 0
