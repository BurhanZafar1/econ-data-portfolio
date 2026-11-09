import numpy as np
import pandas as pd
import pytest

from htn_crosswalk.brfss import plausible, time_matched_cycles, to_proportions

CYCLES = ["2009-2010", "2011-2012", "2013-2014", "2015-2016", "2017-2018"]


def test_se_from_published_interval():
    out = to_proportions(pd.DataFrame({"year": [2017], "prevalence_pct": [30.0],
                                       "lower_pct": [26.08], "upper_pct": [33.92]}))
    assert out["p_self"].iloc[0] == pytest.approx(0.30)
    assert out["se_self"].iloc[0] == pytest.approx(0.02)


def test_time_matched_cycles():
    assert time_matched_cycles(2017, CYCLES, 3) == ["2013-2014", "2015-2016", "2017-2018"]
    assert time_matched_cycles(2012, CYCLES, 2) == ["2009-2010", "2011-2012"]
    assert time_matched_cycles(2012, CYCLES, None) == ["2009-2010", "2011-2012"]
    with pytest.raises(ValueError):
        time_matched_cycles(2010, CYCLES, 3)


def test_suppressed_rows_are_dropped():
    frame = pd.DataFrame({"prevalence_pct": [30.0, np.nan], "lower_pct": [28.0, np.nan], "upper_pct": [32.0, np.nan]})
    assert plausible(frame).tolist() == [True, False]
