"""Rebuild the two committed data files from their official sources.

    python get_data.py

1. data/nhanes_htn_extract.csv.gz from CDC NHANES public XPT files (about
   70 MB, cached in data/raw/, which is not committed).
2. data/brfss_hbp_age_2011_2017.csv from the CDC BRFSS prevalence data API.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from htn_crosswalk.brfss import fetch  # noqa: E402
from htn_crosswalk.extract import build_extract  # noqa: E402

DATA = ROOT / "data"


def _report(path: Path, rows: int) -> None:
    """Print row count and a short checksum so a rebuild can be compared with the committed file."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"Wrote {path.name}: {rows:,} rows, sha256 {digest[:16]}")


def main() -> None:
    extract = build_extract(DATA / "raw")
    nhanes_path = DATA / "nhanes_htn_extract.csv.gz"
    # mtime=0 keeps the gzip bytes identical across rebuilds.
    extract.to_csv(nhanes_path, index=False, compression={"method": "gzip", "mtime": 0})
    _report(nhanes_path, len(extract))

    brfss = fetch()
    brfss_path = DATA / "brfss_hbp_age_2011_2017.csv"
    brfss.to_csv(brfss_path, index=False)
    _report(brfss_path, len(brfss))


if __name__ == "__main__":
    main()
