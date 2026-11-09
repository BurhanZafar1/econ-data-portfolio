"""Known answer: under simple random sampling the paired logit difference has a closed form SE.

With n people, each its own PSU in one stratum and weight 1, linearization gives
Var(d) = 1/(n - 1) * [1/(pm qm) + 1/(ps qs) - 2 (p11 - pm ps) / (pm qm ps qs)],
the delta method for the difference of two correlated logits.
"""

import numpy as np
import pandas as pd
import pytest

from htn_crosswalk.paired import paired_cell, paired_estimates


def _srs_frame(a: int, b: int, c: int, d: int) -> pd.DataFrame:
    """a: self yes and measured yes, b: self yes only, c: measured yes only, d: neither."""
    self_y = [1] * a + [1] * b + [0] * c + [0] * d
    meas_y = [1] * a + [0] * b + [1] * c + [0] * d
    n = len(self_y)
    return pd.DataFrame(
        {
            "cycle": "x", "group": "g", "self_htn": self_y, "measured_htn": meas_y,
            "wt_mec": 1.0, "stratum": 1, "psu": np.arange(n), "analysis": 1,
        }
    )


def test_hand_calculated_two_by_two():
    a, b, c, d = 30, 10, 20, 140
    n = a + b + c + d
    frame = _srs_frame(a, b, c, d)
    out = paired_cell(frame, np.ones(n, dtype=bool))
    ps, pm, p11 = (a + b) / n, (a + c) / n, a / n
    assert out["p_self"] == pytest.approx(ps)
    assert out["p_meas"] == pytest.approx(pm)
    assert out["sens"] == pytest.approx(a / (a + c))
    assert out["spec"] == pytest.approx(d / (b + d))
    assert out["d"] == pytest.approx(np.log(pm / (1 - pm)) - np.log(ps / (1 - ps)))
    qm, qs = pm * (1 - pm), ps * (1 - ps)
    var = (1 / (qm) + 1 / (qs) - 2 * (p11 - pm * ps) / (qm * qs)) / (n - 1)
    assert out["se_d"] == pytest.approx(np.sqrt(var))
    assert out["se_self"] == pytest.approx(np.sqrt(qs / (n - 1)))


def test_identical_definitions_have_zero_difference():
    frame = _srs_frame(25, 0, 0, 75)
    out = paired_cell(frame, np.ones(100, dtype=bool))
    assert out["d"] == pytest.approx(0.0)
    assert out["se_d"] == pytest.approx(0.0, abs=1e-12)


def test_rows_outside_domain_do_not_change_the_point_estimate():
    frame = pd.concat([_srs_frame(30, 10, 20, 140), _srs_frame(5, 5, 5, 5).assign(group="h")])
    frame["psu"] = np.arange(len(frame))
    frame = frame.reset_index(drop=True)
    out = paired_estimates(frame, ["group"]).set_index("group")
    assert out.loc["g", "p_self"] == pytest.approx(40 / 200)
    assert out.loc["h", "n"] == 20
