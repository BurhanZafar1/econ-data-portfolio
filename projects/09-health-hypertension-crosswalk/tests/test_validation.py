"""The held out cycle must not influence its own prediction (no leakage)."""

import numpy as np
import pandas as pd

from htn_crosswalk.validation import predict_one_origin, rolling_origin, score
from htn_crosswalk.extract import XW_LABELS

CYCLES = ("2005-2006", "2007-2008", "2009-2010", "2011-2012")


def _paired(seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for c in CYCLES:
        for g in XW_LABELS:
            for sex in ("Female", "Male"):
                p_self = rng.uniform(0.1, 0.6)
                d = rng.normal(0.1, 0.2)
                rows.append({
                    "cycle": c, "xw_group": g, "sex": sex, "p_self": p_self,
                    "p_meas": 1 / (1 + np.exp(-(np.log(p_self / (1 - p_self)) + d))),
                    "d": d, "se_d": 0.1, "sens": rng.uniform(0.6, 0.9), "spec": rng.uniform(0.85, 0.95),
                })
    return pd.DataFrame(rows)


def test_target_cycle_outcomes_do_not_leak():
    paired = _paired()
    base = predict_one_origin(paired, ["xw_group", "sex"], "2011-2012")
    tampered = paired.copy()
    target = tampered["cycle"] == "2011-2012"
    tampered.loc[target, ["d", "sens", "spec", "p_meas"]] = [9.0, 0.01, 0.02, 0.99]
    again = predict_one_origin(tampered, ["xw_group", "sex"], "2011-2012")
    for col in ("rogan_gladen", "rogan_gladen_latest_3", "crosswalk_all_cycles", "crosswalk_latest_3", "crosswalk_linear_trend"):
        np.testing.assert_allclose(base[col], again[col])


def test_rolling_origin_needs_three_earlier_cycles():
    preds = rolling_origin(_paired(), ["xw_group", "sex"])
    assert set(preds["cycle"]) == {"2011-2012"}
    assert (preds["n_train_cycles"] == 3).all()
    scores = score(preds)
    assert len(scores) == 6 and scores["mae_pp"].ge(0).all()
