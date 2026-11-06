"""Load the two FEBRL 4 files and recover the true links for evaluation only.

FEBRL 4 is a synthetic benchmark: 5,000 generated "original" records in file A
and one corrupted duplicate of each in file B (typos, missing fields, swapped
values). No record describes a real person. The generator's record id
(rec-1070-org in A, rec-1070-dup-0 in B) tells us which pairs are true
matches; the linkage itself never looks at it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

FIELDS = [
    "given_name",
    "surname",
    "street_number",
    "address_1",
    "address_2",
    "suburb",
    "postcode",
    "state",
    "date_of_birth",
]


def load_file(path: Path) -> pd.DataFrame:
    """Read one FEBRL file as strings, with blanks as missing, indexed by rec_id."""
    frame = pd.read_csv(path, dtype=str, skipinitialspace=True, keep_default_na=False)
    frame = frame.set_index("rec_id")[FIELDS]
    return frame.apply(lambda column: column.str.strip().str.lower()).replace("", pd.NA)


def entity_id(rec_ids: pd.Index) -> pd.Series:
    """The generator's entity number, e.g. rec-1070-dup-0 -> 1070."""
    return pd.Series(rec_ids.str.split("-").str[1].astype(int), index=rec_ids)


def true_links(left: pd.DataFrame, right: pd.DataFrame) -> pd.MultiIndex:
    """All (A, B) record pairs that describe the same generated entity."""
    left_ids = entity_id(left.index).rename("entity").reset_index()
    right_ids = entity_id(right.index).rename("entity").reset_index()
    merged = left_ids.merge(right_ids, on="entity", suffixes=("_a", "_b"))
    return pd.MultiIndex.from_frame(merged[["rec_id_a", "rec_id_b"]], names=["a", "b"])
