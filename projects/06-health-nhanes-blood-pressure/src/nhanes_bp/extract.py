"""Download NHANES public use files and build a person level blood pressure extract.

Three files per two year cycle are merged on SEQN:
  DEMO  demographics, exam status, MEC exam weight, design strata and PSUs
  BPX   examination blood pressure (auscultatory, up to four readings)
  BPQ   blood pressure questionnaire (current antihypertensive medication)

Cycles 1999-2000 to 2017-2018 all use the same auscultatory protocol. Later
cycles (2017-March 2020 pre pandemic file, 2021-2023) switched to an
oscillometric device (BPXO), so they are not pooled into this series.
"""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{name}.xpt"


@dataclass(frozen=True)
class Cycle:
    """One two year NHANES cycle and the file suffix CDC uses for it."""

    label: str
    start_year: int
    suffix: str

    def file_name(self, stem: str) -> str:
        return f"{stem}{self.suffix}"


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
BPQ_COLS = ["SEQN", "BPQ040A", "BPQ050A"]


def download_cycle(cycle: Cycle, raw_dir: Path) -> dict[str, Path]:
    """Fetch the three XPT files for a cycle into raw_dir (skips files already present)."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for stem in ("DEMO", "BPX", "BPQ"):
        name = cycle.file_name(stem)
        dest = raw_dir / f"{name}.xpt"
        if not dest.exists():
            url = BASE_URL.format(year=cycle.start_year, name=name)
            request = urllib.request.Request(url, headers={"User-Agent": "nhanes-bp-extract/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response:
                dest.write_bytes(response.read())
        paths[stem] = dest
    return paths


def average_readings(sbp: pd.DataFrame, dbp: pd.DataFrame) -> pd.DataFrame:
    """Average up to three readings, following the NCHS hypertension data briefs.

    Systolic and diastolic readings are selected separately (they are almost
    always missing in pairs). Readings 1 to 3 are the protocol readings; reading 4 exists only when one
    of them could not be obtained, so the first three non missing readings of
    1 to 4 are used. A diastolic reading of 0 mmHg (sound audible to zero) is
    dropped from the diastolic average unless every diastolic reading is 0.
    """
    sbp_vals = sbp.to_numpy(dtype=float)
    dbp_vals = dbp.to_numpy(dtype=float)
    first_three = _first_k_non_missing(sbp_vals, k=3)
    sbp_mean = _row_mean(np.where(first_three, sbp_vals, np.nan))
    n_readings = first_three.sum(axis=1)

    dbp_first_three = _first_k_non_missing(dbp_vals, k=3)
    dbp_used = np.where(dbp_first_three, dbp_vals, np.nan)
    nonzero = np.where(dbp_used > 0, dbp_used, np.nan)
    has_nonzero = np.isfinite(nonzero).any(axis=1)
    has_any = np.isfinite(dbp_used).any(axis=1)
    dbp_mean = np.where(has_nonzero, _row_mean(nonzero), np.where(has_any, 0.0, np.nan))
    return pd.DataFrame(
        {"sbp": sbp_mean, "dbp": dbp_mean, "n_readings": n_readings},
        index=sbp.index,
    )


def _row_mean(values: np.ndarray) -> np.ndarray:
    """Mean of the finite entries in each row; NaN for rows with none."""
    finite = np.isfinite(values)
    count = finite.sum(axis=1)
    total = np.where(finite, values, 0.0).sum(axis=1)
    return np.divide(total, count, out=np.full(len(values), np.nan), where=count > 0)


def _first_k_non_missing(values: np.ndarray, k: int) -> np.ndarray:
    """Boolean mask selecting the first k finite entries of each row."""
    finite = np.isfinite(values)
    return finite & (np.cumsum(finite, axis=1) <= k)


def build_cycle_extract(cycle: Cycle, paths: dict[str, Path]) -> pd.DataFrame:
    """Merge DEMO, BPX and BPQ for one cycle into one row per examined person aged 18+."""
    demo = pd.read_sas(paths["DEMO"], format="xport")[DEMO_COLS]
    bpx = pd.read_sas(paths["BPX"], format="xport")[["SEQN", *SBP_COLS, *DBP_COLS]]
    bpq = pd.read_sas(paths["BPQ"], format="xport")[BPQ_COLS]

    demo = demo[(demo["RIDSTATR"] == 2) & (demo["RIDAGEYR"] >= 18)]
    merged = demo.merge(bpx, on="SEQN", how="left").merge(bpq, on="SEQN", how="left")
    averaged = average_readings(merged[SBP_COLS], merged[DBP_COLS])

    # BPQ050A (now taking prescribed BP medicine) is asked only when BPQ040A == 1
    # (told to take medicine). People never asked, because BPQ020 or BPQ040A was
    # "no", missing, refused or don't know, are coded as not taking medication, as
    # NCHS does; only a refused or don't know answer to BPQ050A itself is unknown.
    on_med = (merged["BPQ050A"] == 1).astype(int)
    med_known = merged["BPQ050A"].isin([1, 2]) | ~(merged["BPQ040A"] == 1)

    out = pd.DataFrame(
        {
            "cycle": cycle.label,
            "seqn": merged["SEQN"].astype(int),
            "age": merged["RIDAGEYR"].astype(int),
            "sex": merged["RIAGENDR"].map({1: "Male", 2: "Female"}),
            "pregnant": (merged["RIDEXPRG"] == 1).astype(int),
            "wt_mec": merged["WTMEC2YR"].astype(float),
            "stratum": merged["SDMVSTRA"].astype(int),
            "psu": merged["SDMVPSU"].astype(int),
            "sbp": averaged["sbp"].round(4),
            "dbp": averaged["dbp"].round(4),
            "n_readings": averaged["n_readings"].astype(int),
            "bp_med": on_med.where(med_known),
        }
    )
    return out.reset_index(drop=True)


def build_extract(raw_dir: Path) -> pd.DataFrame:
    """Download (if needed) and stack all ten cycles."""
    frames = [build_cycle_extract(c, download_cycle(c, raw_dir)) for c in CYCLES]
    return pd.concat(frames, ignore_index=True)
