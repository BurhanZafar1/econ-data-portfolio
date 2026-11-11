"""Build the two analysis inputs from official public files.

1. NHANES 2017-2018 examination microdata (CDC): one row per examined adult aged
   40+ with mean systolic blood pressure (SBP), sex, exam weight, stratum and PSU.
2. WHO Mortality Database, ICD-10 part 5: United States ischemic heart disease
   (IHD, ICD-10 I20 to I25) deaths in 2018 by sex and age group.
"""

from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from sbp_paf import AGE_LABELS

NHANES_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/{name}.xpt"
WHO_URL = (
    "https://cdn.who.int/media/docs/default-source/world-health-data-platform/"
    "mortality-raw-data/morticd10_part5.zip"
)
WHO_USA_CODE = "2450"  # WHO Mortality Database country code for the United States
DEATH_YEAR = "2018"
MIN_AGE = 40
AGE_BREAKS: tuple[int, ...] = (40, 50, 60, 70, 80, 200)

# WHO full age format (Frmat 00): Deaths14 = 40-44 ... Deaths22 = 80-84,
# Deaths23 = 85-89, Deaths24 = 90-94, Deaths25 = 95+ (mort_documentation, March 2021).
WHO_AGE_COLUMNS: dict[str, tuple[str, ...]] = {
    "40-49": ("Deaths14", "Deaths15"),
    "50-59": ("Deaths16", "Deaths17"),
    "60-69": ("Deaths18", "Deaths19"),
    "70-79": ("Deaths20", "Deaths21"),
    "80+": ("Deaths22", "Deaths23", "Deaths24", "Deaths25"),
}
SEX_CODES = {"1": "Male", "2": "Female"}


def _fetch(url: str, dest: Path) -> Path:
    """Download url to dest unless the file is already cached."""
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "sbp-paf/1.0"})
        with urllib.request.urlopen(request, timeout=300) as response:
            dest.write_bytes(response.read())
    return dest


def age_group(age: pd.Series) -> pd.Series:
    """Ten year groups 40-49 to 80+ (NHANES top codes age at 80)."""
    return pd.cut(age, bins=list(AGE_BREAKS), right=False, labels=list(AGE_LABELS)).astype(str)


def mean_sbp(readings: pd.DataFrame) -> pd.Series:
    """Mean of the first three non missing SBP readings of 1 to 4 (NCHS convention).

    Reading 4 exists only when one of readings 1 to 3 failed.
    """
    values = readings.to_numpy(dtype=float)
    finite = np.isfinite(values)
    used = finite & (np.cumsum(finite, axis=1) <= 3)
    count = used.sum(axis=1)
    total = np.where(used, values, 0.0).sum(axis=1)
    out = np.divide(total, count, out=np.full(len(values), np.nan), where=count > 0)
    return pd.Series(out, index=readings.index)


def build_nhanes(raw_dir: Path) -> pd.DataFrame:
    """Examined, non pregnant adults 40+ with at least one SBP reading."""
    demo = pd.read_sas(_fetch(NHANES_URL.format(name="DEMO_J"), raw_dir / "DEMO_J.xpt"), format="xport")
    bpx = pd.read_sas(_fetch(NHANES_URL.format(name="BPX_J"), raw_dir / "BPX_J.xpt"), format="xport")
    frame = demo.merge(bpx, on="SEQN", how="left", validate="one_to_one")
    frame["sbp"] = mean_sbp(frame[[f"BPXSY{i}" for i in range(1, 5)]])
    eligible = (
        (frame["RIDSTATR"] == 2)  # interviewed and examined in the MEC
        & (frame["RIDAGEYR"] >= MIN_AGE)
        & (frame["RIDEXPRG"] != 1)  # not pregnant at exam
        & (frame["WTMEC2YR"] > 0)
    )
    keep = eligible & frame["sbp"].notna()
    out = pd.DataFrame(
        {
            "seqn": frame["SEQN"].astype(int),
            "age": frame["RIDAGEYR"].astype(int),
            "sex": frame["RIAGENDR"].map({1.0: "Male", 2.0: "Female"}),
            "wt_mec": frame["WTMEC2YR"],
            "stratum": frame["SDMVSTRA"].astype(int),
            "psu": frame["SDMVPSU"].astype(int),
            "sbp": frame["sbp"].round(4),
        }
    )[keep.to_numpy()]
    out = out.reset_index(drop=True)
    out.attrs["n_excluded_no_sbp"] = int((eligible & frame["sbp"].isna()).sum())
    return out


def parse_who_ihd(raw_file: io.TextIOBase | Path) -> pd.DataFrame:
    """US IHD deaths (ICD-10 I20 to I25) in 2018 by sex and age group from a WHO part file."""
    raw = pd.read_csv(raw_file, dtype=str)
    usa = raw[(raw["Country"] == WHO_USA_CODE) & (raw["Year"] == DEATH_YEAR) & raw["Admin1"].isna()]
    if set(usa["Frmat"]) != {"00"}:
        raise ValueError(f"Unexpected WHO age format(s): {sorted(set(usa['Frmat']))}")
    ihd = usa[usa["Cause"].str.match(r"^I2[0-5]")].copy()
    death_cols = [f"Deaths{i}" for i in range(1, 27)]
    ihd[death_cols] = ihd[death_cols].apply(pd.to_numeric).fillna(0).astype(int)
    rows = []
    for code, sex in SEX_CODES.items():
        by_sex = ihd[ihd["Sex"] == code]
        for label, cols in WHO_AGE_COLUMNS.items():
            rows.append({"sex": sex, "age_group": label, "deaths": int(by_sex[list(cols)].sum().sum())})
        rows.append({"sex": sex, "age_group": "all ages", "deaths": int(by_sex["Deaths1"].sum())})
    return pd.DataFrame(rows)


def build_who(raw_dir: Path) -> pd.DataFrame:
    """Download (or reuse) the WHO part 5 archive and extract US IHD deaths for 2018."""
    archive = _fetch(WHO_URL, raw_dir / "morticd10_part5.zip")
    with zipfile.ZipFile(archive) as zf:
        (name,) = zf.namelist()
        with zf.open(name) as handle:
            return parse_who_ihd(io.TextIOWrapper(handle, encoding="latin-1"))
