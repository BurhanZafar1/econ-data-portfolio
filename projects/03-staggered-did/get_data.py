"""Rebuild data/ from the official package repositories: python get_data.py.

The two CSV files in data/ are committed so the project runs offline. This
script shows exactly where they came from and regenerates them.
"""

from __future__ import annotations

import tempfile
import urllib.request
from pathlib import Path

import pyreadr

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "mpdta": "https://raw.githubusercontent.com/bcallaway11/did/master/data/mpdta.rda",
    "math_reform": (
        "https://raw.githubusercontent.com/evanjflack/bacondecomp/master/data/math_reform.rda"
    ),
}


def fetch(name: str, url: str, out_dir: Path) -> None:
    """Download one .rda file and write it to out_dir as a CSV."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{name}.rda"
        urllib.request.urlretrieve(url, path)
        frame = pyreadr.read_r(str(path))[name]
    frame.to_csv(out_dir / f"{name}.csv", index=False)
    print(f"{name}: {len(frame)} rows")


def main() -> None:
    (ROOT / "data").mkdir(exist_ok=True)
    for name, url in SOURCES.items():
        fetch(name, url, ROOT / "data")


if __name__ == "__main__":
    main()
