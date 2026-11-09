"""Build a person level NHANES extract with self reported and measured hypertension.

Three public files per two year cycle are merged on SEQN:
  DEMO  demographics, exam status, MEC exam weight, design strata and PSUs
  BPX   examination blood pressure (auscultatory, up to four readings)
  BPQ   blood pressure questionnaire (ever told, told to take and taking medicine)

Every examined adult (18+) answers both definitions, so each person carries a
paired observation: the self reported answer and the measured status.
"""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{name}.xpt"

# BRFSS publishes state estimates in these age groups, so the crosswalk uses them too.
AGE_BREAKS: tuple[int, ...] = (18, 25, 35, 45, 55, 65, 200)
AGE_LABELS: tuple[str, ...] = ("18-24", "25-34", "35-44", "45-54", "55-64", "65+")
# The crosswalk pools 18-34: women aged 18-24 have a median of 3.5 measured cases
# per cycle, too few for a stable logit difference. Each BRFSS group maps to one.
XW_LABELS: tuple[str, ...] = ("18-34", "35-44", "45-54", "55-64", "65+")
XW_GROUP: dict[str, str] = {"18-24": "18-34", "25-34": "18-34", **{a: a for a in AGE_LABELS[2:]}}


@dataclass(frozen=True)
class Cycle:
    """One two year NHANES cycle, its first calendar year and CDC file suffix."""

    label: str
    start_year: int
    suffix: str


CYCLES: tuple[Cycle, ...] = (
    Cycle("1999-2000", 1999, ""),
    Cycle("2001-2002", 2001, "_B"),
    Cycle("2003-2004", 2003, "_C"),
    Cycle("2005-2006", 2005, "_D"),
    Cycle("2007-2008", 2007, "_E"),
    Cycle("2009-2010", 2009, "_F"),
    Cycle("2011-2012", 2011, "_G"),
    Cycle("2013-2014", 2013, "_H"),
    Cycle("2015-2016", 2015, "_I"),
    Cycle("2017-2018", 2017, "_J"),
)

DEMO_COLS = ["SEQN", "RIDSTATR", "RIAGENDR", "RIDAGEYR", "RIDEXPRG", "WTMEC2YR", "SDMVSTRA", "SDMVPSU"]
SBP_COLS = [f"BPXSY{i}" for i in range(1, 5)]
DBP_COLS = [f"BPXDI{i}" for i in range(1, 5)]
BPQ_COLS = ["SEQN", "BPQ020", "BPQ040A", "BPQ050A"]


def download_cycle(cycle: Cycle, raw_dir: Path) -> dict[str, Path]:
    """Fetch the three XPT files for a cycle into raw_dir (skips files already present)."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for stem in ("DEMO", "BPX", "BPQ"):
        name = f"{stem}{cycle.suffix}"
        dest = raw_dir / f"{name}.xpt"
        if not dest.exists():
            url = BASE_URL.format(year=cycle.start_year, name=name)
            request = urllib.request.Request(url, headers={"User-Agent": "htn-crosswalk/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response:
                dest.write_bytes(response.read())
        paths[stem] = dest
    return paths


def average_readings(sbp: pd.DataFrame, dbp: pd.DataFrame) -> pd.DataFrame:
    """Average up to three readings, following the NCHS hypertension data briefs.

    The first three non missing readings of 1 to 4 are used (reading 4 exists
    only when one of 1 to 3 failed). A diastolic 0 mmHg is dropped from the
    diastolic average unless every diastolic reading is 0.
    """
    sbp_vals = sbp.to_numpy(dtype=float)
    dbp_vals = dbp.to_numpy(dtype=float)
    sbp_mean = _row_mean(np.where(_first_k_finite(sbp_vals, 3), sbp_vals, np.nan))
    dbp_used = np.where(_first_k_finite(dbp_vals, 3), dbp_vals, np.nan)
    nonzero = np.where(dbp_used > 0, dbp_used, np.nan)
    has_nonzero = np.isfinite(nonzero).any(axis=1)
    has_any = np.isfinite(dbp_used).any(axis=1)
    dbp_mean = np.where(has_nonzero, _row_mean(nonzero), np.where(has_any, 0.0, np.nan))
    return pd.DataFrame({"sbp": sbp_mean, "dbp": dbp_mean}, index=sbp.index)


def _row_mean(values: np.ndarray) -> np.ndarray:
    """Mean of the finite entries in each row; NaN for rows with none."""
    finite = np.isfinite(values)
    count = finite.sum(axis=1)
    total = np.where(finite, values, 0.0).sum(axis=1)
    return np.divide(total, count, out=np.full(len(values), np.nan), where=count > 0)


def _first_k_finite(values: np.ndarray, k: int) -> np.ndarray:
    """Boolean mask selecting the first k finite entries of each row."""
    finite = np.isfinite(values)
    return finite & (np.cumsum(finite, axis=1) <= k)


def classify(frame: pd.DataFrame) -> pd.DataFrame:
    """Add the two hypertension definitions and the analysis flag.

    measured_htn: mean SBP >= 140 or mean DBP >= 90 mmHg or now taking
        prescribed medicine (BPQ050A). This is the NCD-RisC and WHO definition.
    self_htn: answered yes to BPQ020, "ever told by a doctor or other health
        professional that you had hypertension".
    BPQ050A is asked only of people told to take medicine (BPQ040A == 1), who
    were first told they had hypertension (BPQ020 == 1). People never asked are
    not taking medicine, as NCHS codes them.
    """
    out = frame.copy()
    self_known = out["BPQ020"].isin([1, 2])
    med_known = out["BPQ050A"].isin([1, 2]) | ~(out["BPQ040A"] == 1)
    bp_known = out["sbp"].notna() & out["dbp"].notna()
    on_med = out["BPQ050A"] == 1
    high_reading = (out["sbp"] >= 140) | (out["dbp"] >= 90)

    out["self_htn"] = (out["BPQ020"] == 1).astype(float).where(self_known)
    out["measured_htn"] = (high_reading | on_med).astype(float).where(bp_known & med_known)
    out["analysis"] = (
        (out["RIDSTATR"] == 2)
        & (out["RIDAGEYR"] >= 18)
        & (out["RIDEXPRG"] != 1)
        & self_known
        & bp_known
        & med_known
        & (out["WTMEC2YR"] > 0)
    )
    return out


def build_cycle_extract(cycle: Cycle, paths: dict[str, Path]) -> pd.DataFrame:
    """Merge DEMO, BPX and BPQ for one cycle; keep every examined adult for the design."""
    demo = pd.read_sas(paths["DEMO"], format="xport")[DEMO_COLS]
    bpx = pd.read_sas(paths["BPX"], format="xport")[["SEQN", *SBP_COLS, *DBP_COLS]]
    bpq = pd.read_sas(paths["BPQ"], format="xport")[BPQ_COLS]

    demo = demo[(demo["RIDSTATR"] == 2) & (demo["RIDAGEYR"] >= 18)]
    merged = demo.merge(bpx, on="SEQN", how="left").merge(bpq, on="SEQN", how="left")
    merged = pd.concat([merged, average_readings(merged[SBP_COLS], merged[DBP_COLS])], axis=1)
    merged = classify(merged)

    return pd.DataFrame(
        {
            "cycle": cycle.label,
            "seqn": merged["SEQN"].astype(int),
            "age": merged["RIDAGEYR"].astype(int),
            "sex": merged["RIAGENDR"].map({1: "Male", 2: "Female"}),
            "wt_mec": merged["WTMEC2YR"].astype(float),
            "stratum": merged["SDMVSTRA"].astype(int),
            "psu": merged["SDMVPSU"].astype(int),
            "sbp": merged["sbp"].round(4),
            "dbp": merged["dbp"].round(4),
            "self_htn": merged["self_htn"],
            "measured_htn": merged["measured_htn"],
            "analysis": merged["analysis"].astype(int),
        }
    ).reset_index(drop=True)


def build_extract(raw_dir: Path) -> pd.DataFrame:
    """Download (if needed) and stack all ten cycles."""
    frames = [build_cycle_extract(c, download_cycle(c, raw_dir)) for c in CYCLES]
    return pd.concat(frames, ignore_index=True)


def add_age_group(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach the BRFSS age group and the (coarser) crosswalk age group."""
    out = frame.copy()
    out["age_group"] = pd.cut(
        out["age"], bins=list(AGE_BREAKS), right=False, labels=list(AGE_LABELS)
    ).astype(str)
    out["xw_group"] = out["age_group"].map(XW_GROUP)
    return out
