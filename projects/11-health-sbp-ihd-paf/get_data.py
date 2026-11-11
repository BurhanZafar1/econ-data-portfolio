"""Rebuild the two committed data files from the official sources.

    python get_data.py

Writes data/nhanes_sbp_2017_2018.csv.gz (CDC NHANES) and
data/who_us_ihd_deaths_2018.csv (WHO Mortality Database). Raw downloads
(about 15 MB) are cached in data/raw/, which is not committed.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from sbp_paf.extract import build_nhanes, build_who  # noqa: E402

DATA = ROOT / "data"
RAW = DATA / "raw"


def _report(path: Path, rows: int) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"Wrote {path.name}: {rows:,} rows, sha256 {digest[:16]}")


def main() -> None:
    nhanes = build_nhanes(RAW)
    nhanes_path = DATA / "nhanes_sbp_2017_2018.csv.gz"
    # mtime=0 keeps the gzip bytes identical across rebuilds.
    nhanes.to_csv(nhanes_path, index=False, compression={"method": "gzip", "mtime": 0})
    _report(nhanes_path, len(nhanes))
    print(f"Excluded {nhanes.attrs['n_excluded_no_sbp']} examined adults 40+ with no SBP reading")

    deaths = build_who(RAW)
    deaths_path = DATA / "who_us_ihd_deaths_2018.csv"
    deaths.to_csv(deaths_path, index=False)
    _report(deaths_path, len(deaths))


if __name__ == "__main__":
    main()
