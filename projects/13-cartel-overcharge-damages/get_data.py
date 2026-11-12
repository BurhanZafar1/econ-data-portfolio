"""Download the Joint Executive Committee weekly data and verify it.

The file is the AER R package's `CartelStability` data (Porter 1983, as
distributed with Stock and Watson's textbook), served by the Rdatasets
archive. A copy is committed in data/, so this script is only needed to
re-fetch and confirm that the committed copy matches the public source.

Usage:  python get_data.py
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

URL = (
    "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/"
    "master/csv/AER/CartelStability.csv"
)
TARGET = Path(__file__).resolve().parent / "data" / "CartelStability.csv"
EXPECTED_SHA256 = "adc6d1873d0ee299e2067e2546c2ddc1ef1787905d8a2857df2a221e2c58ca0a"


def sha256(content: bytes) -> str:
    """Hex SHA-256 digest of a byte string."""
    return hashlib.sha256(content).hexdigest()


def main() -> int:
    with urllib.request.urlopen(URL, timeout=60) as response:
        content = response.read()
    digest = sha256(content)
    if digest != EXPECTED_SHA256:
        print(f"Warning: downloaded file hash {digest} differs from the committed copy.")
        print("The upstream file may have changed; inspect it before overwriting.")
        return 1
    TARGET.write_bytes(content)
    print(f"Saved {TARGET.name} ({len(content):,} bytes), hash verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
