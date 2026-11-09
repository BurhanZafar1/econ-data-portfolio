from pathlib import Path

import numpy as np
import pandas as pd

from htn_crosswalk.extract import add_age_group, average_readings, classify

DATA = Path(__file__).resolve().parents[1] / "data"


def _person(**kw) -> dict:
    base = dict(RIDSTATR=2, RIDAGEYR=40, RIDEXPRG=np.nan, WTMEC2YR=1000.0, BPQ020=2,
                BPQ040A=np.nan, BPQ050A=np.nan, sbp=120.0, dbp=70.0)
    return {**base, **kw}


def test_classification_rules():
    frame = classify(pd.DataFrame([
        _person(),                                                    # normal, not told
        _person(sbp=150.0),                                           # high reading, not told
        _person(BPQ020=1, BPQ040A=1, BPQ050A=1),                      # controlled on medicine
        _person(BPQ020=1, BPQ040A=2),                                 # told, no medicine, normal now
        _person(BPQ020=9),                                            # self report unknown
        _person(RIDEXPRG=1),                                          # pregnant
        _person(BPQ020=1, BPQ040A=1, BPQ050A=9),                      # medicine status unknown
    ]))
    assert frame["self_htn"].tolist()[:4] == [0, 0, 1, 1]
    assert frame["measured_htn"].tolist()[:4] == [0, 1, 1, 0]
    assert frame["analysis"].tolist() == [True, True, True, True, False, False, False]


def test_diastolic_zero_rule_and_first_three_readings():
    sbp = pd.DataFrame([[120, 124, np.nan, 128], [130, 132, 134, 200]], dtype=float)
    dbp = pd.DataFrame([[0, 80, np.nan, 70], [0, 0, 0, np.nan]], dtype=float)
    out = average_readings(sbp, dbp)
    assert out["sbp"].tolist() == [124.0, 132.0]
    assert out["dbp"].tolist() == [75.0, 0.0]


def test_age_groups():
    out = add_age_group(pd.DataFrame({"age": [18, 24, 25, 34, 35, 64, 65, 85]}))
    assert out["age_group"].tolist() == ["18-24", "18-24", "25-34", "25-34", "35-44", "55-64", "65+", "65+"]
    assert out["xw_group"].tolist()[:4] == ["18-34"] * 4


def test_committed_extract():
    extract = pd.read_csv(DATA / "nhanes_htn_extract.csv.gz")
    assert len(extract) == 56_367
    assert extract["analysis"].sum() == 52_009
    assert extract["cycle"].nunique() == 10
    analysed = extract[extract["analysis"] == 1]
    assert analysed[["self_htn", "measured_htn"]].isin([0, 1]).all().all()
