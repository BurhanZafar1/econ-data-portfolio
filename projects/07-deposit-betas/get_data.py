"""Download the raw FRED series used by this project into data/raw/.

    python get_data.py

The committed copies in data/raw/ were downloaded on 2026-11-08. Running this script
replaces them with the latest vintage, so later numbers can differ slightly from the
README (FRED revises the funds rate rarely and the FDIC rates almost never).
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from deposit_beta.data import ALL_SERIES  # noqa: E402

RAW = ROOT / "data" / "raw"
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"


def download(series: str, target: Path) -> None:
    """Fetch one fredgraph.csv file and check that it looks like FRED output."""
    with urllib.request.urlopen(URL.format(series=series), timeout=60) as response:
        text = response.read().decode("utf-8")
    header = text.splitlines()[0]
    if not header.endswith(series):
        raise RuntimeError(f"unexpected response for {series}: {header[:80]!r}")
    target.write_text(text, encoding="utf-8")


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for series in ALL_SERIES:
        target = RAW / f"{series}.csv"
        download(series, target)
        rows = len(target.read_text(encoding="utf-8").splitlines()) - 1
        print(f"{series:<10} {rows:>6} rows -> {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
