"""Rebuild data/nhanes_bp_extract.csv.gz from the official CDC NHANES files.

    python get_data.py

Raw XPT files (about 70 MB) are cached in data/raw/, which is not committed.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from nhanes_bp.extract import build_extract  # noqa: E402

DATA = ROOT / "data"
EXTRACT = DATA / "nhanes_bp_extract.csv.gz"


def main() -> None:
    extract = build_extract(DATA / "raw")
    # mtime=0 keeps the gzip bytes identical across rebuilds.
    extract.to_csv(EXTRACT, index=False, compression={"method": "gzip", "mtime": 0})
    digest = hashlib.sha256(EXTRACT.read_bytes()).hexdigest()
    print(f"Wrote {EXTRACT.name}: {len(extract):,} rows, sha256 {digest[:16]}")


if __name__ == "__main__":
    main()
