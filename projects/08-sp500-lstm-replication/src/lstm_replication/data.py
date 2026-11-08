"""Load the raw S&P 500 file and cut the sample windows used in the project."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# The notebook asked Yahoo for 1 Jan 1980 to 28 Feb 2019. The 2019 download tool returned
# 31 Dec 1979 to 27 Feb 2019 (one trading day earlier at both ends): the notebook's feature
# table runs from 31 Jul 1981 to 28 Jan 2019, which only this window reproduces.
PAPER_START = "1979-12-31"
PAPER_END = "2019-02-27"
PAPER_RAW_ROWS = 9875  # rows the original notebook printed after the download


def load_raw(path: Path) -> pd.DataFrame:
    """Daily close and volume indexed by date, sorted, no duplicates."""
    frame = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    if frame.index.has_duplicates:
        raise ValueError("duplicate dates in raw file")
    return frame[["close", "volume"]]


def window(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Rows between start and end, both inclusive."""
    return frame.loc[start:end]
