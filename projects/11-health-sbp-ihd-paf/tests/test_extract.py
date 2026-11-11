"""Tests for data extraction and for the committed data files."""

import io
from pathlib import Path

import numpy as np
import pandas as pd

from sbp_paf import AGE_LABELS
from sbp_paf.extract import age_group, mean_sbp, parse_who_ihd

DATA = Path(__file__).resolve().parents[1] / "data"


def test_mean_sbp_uses_first_three_readings():
    readings = pd.DataFrame({"BPXSY1": [120, np.nan, np.nan], "BPXSY2": [124, 130, np.nan],
                             "BPXSY3": [128, 134, np.nan], "BPXSY4": [200, 138, np.nan]})
    out = mean_sbp(readings)
    assert out.iloc[0] == 124.0  # reading 4 ignored when 1 to 3 exist
    assert out.iloc[1] == 134.0  # reading 4 replaces the failed reading 1
    assert np.isnan(out.iloc[2])


def test_age_groups():
    assert list(age_group(pd.Series([40, 49, 50, 79, 80]))) == ["40-49", "40-49", "50-59", "70-79", "80+"]


def test_who_parser_on_a_synthetic_file():
    header = "Country,Admin1,SubDiv,Year,List,Cause,Sex,Frmat,IM_Frmat," + ",".join(
        [f"Deaths{i}" for i in range(1, 27)] + [f"IM_Deaths{i}" for i in range(1, 5)])

    def row(cause, sex, year="2018"):
        deaths = [0] * 26
        deaths[13], deaths[21], deaths[24] = 1, 10, 100  # 40-44, 80-84, 95+
        deaths[0] = 111
        return ",".join(["2450", "", "", year, "104", cause, sex, "00", "01"] + [str(d) for d in deaths] + ["0"] * 4)

    text = "\n".join([header, row("I210", "1"), row("I251", "1"), row("I64", "1"),
                      row("I210", "2"), row("I210", "1", year="2017")])
    out = parse_who_ihd(io.StringIO(text)).set_index(["sex", "age_group"])["deaths"]
    assert out[("Male", "40-49")] == 2  # two IHD rows, stroke (I64) and 2017 excluded
    assert out[("Male", "80+")] == 220
    assert out[("Female", "80+")] == 110
    assert out[("Male", "all ages")] == 222


def test_committed_data_shapes():
    nh = pd.read_csv(DATA / "nhanes_sbp_2017_2018.csv.gz")
    assert nh["seqn"].is_unique and nh["age"].min() >= 40
    assert set(nh["sex"]) == {"Male", "Female"}
    assert nh.groupby("stratum")["psu"].nunique().min() >= 2
    deaths = pd.read_csv(DATA / "who_us_ihd_deaths_2018.csv")
    for sex in ("Male", "Female"):
        d = deaths[deaths["sex"] == sex].set_index("age_group")["deaths"]
        assert d[list(AGE_LABELS)].sum() <= d["all ages"]


def test_who_parser_maps_every_age_column():
    # Put a distinct power of two in each of Deaths11 to Deaths26 so every column is identifiable.
    header = "Country,Admin1,SubDiv,Year,List,Cause,Sex,Frmat,IM_Frmat," + ",".join(
        [f"Deaths{i}" for i in range(1, 27)] + [f"IM_Deaths{i}" for i in range(1, 5)])
    deaths = [0] * 26
    for i in range(11, 27):
        deaths[i - 1] = 2 ** (i - 11)
    deaths[0] = sum(deaths)
    row = ",".join(["2450", "", "", "2018", "104", "I251", "2", "00", "01"] + [str(d) for d in deaths] + ["0"] * 4)
    out = parse_who_ihd(io.StringIO(header + "\n" + row)).set_index(["sex", "age_group"])["deaths"]
    p = {i: 2 ** (i - 11) for i in range(11, 27)}
    assert out[("Female", "40-49")] == p[14] + p[15]
    assert out[("Female", "50-59")] == p[16] + p[17]
    assert out[("Female", "60-69")] == p[18] + p[19]
    assert out[("Female", "70-79")] == p[20] + p[21]
    assert out[("Female", "80+")] == p[22] + p[23] + p[24] + p[25]  # unknown age (Deaths26) excluded
