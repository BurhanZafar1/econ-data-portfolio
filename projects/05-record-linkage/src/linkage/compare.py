"""Turn each candidate pair into a comparison vector of agreement levels.

Every field gets a small number of ordered levels, highest means agree:
0 disagree, 1 agree for exact fields; 0 disagree, 1 partial, 2 agree for the
rest. A missing value on either side gives a
missing level, which the model treats as uninformative (Enamorado, Fifield
and Imai 2019). String cutoffs 0.94 and 0.88 on Jaro-Winkler are the defaults
in that paper.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .strings import jaro_winkler

AGREE_CUTOFF = 0.94
PARTIAL_CUTOFF = 0.88
DISAGREE, PARTIAL, AGREE = 0, 1, 2

LevelFunction = Callable[[str, str], int]


def string_level(left: str, right: str) -> int:
    """Three levels from Jaro-Winkler similarity."""
    score = jaro_winkler(left, right)
    if score >= AGREE_CUTOFF:
        return AGREE
    if score >= PARTIAL_CUTOFF:
        return PARTIAL
    return DISAGREE


def exact_level(left: str, right: str) -> int:
    """Two levels: 1 if identical, else 0."""
    return 1 if left == right else DISAGREE


def one_digit_level(left: str, right: str) -> int:
    """Codes of equal length: identical, one position different, or more."""
    if left == right:
        return AGREE
    if len(left) == len(right) and sum(a != b for a, b in zip(left, right)) == 1:
        return PARTIAL
    return DISAGREE


def date_level(left: str, right: str) -> int:
    """Dates as YYYYMMDD: identical, exactly one of year, month, day differs, or more."""
    if left == right:
        return AGREE
    parts_left = (left[:4], left[4:6], left[6:])
    parts_right = (right[:4], right[4:6], right[6:])
    if sum(a != b for a, b in zip(parts_left, parts_right)) == 1:
        return PARTIAL
    return DISAGREE


@dataclass(frozen=True)
class FieldRule:
    """How one field is compared and how many levels it has."""

    field: str
    level: LevelFunction
    n_levels: int


FIELD_RULES: tuple[FieldRule, ...] = (
    FieldRule("given_name", string_level, 3),
    FieldRule("surname", string_level, 3),
    FieldRule("street_number", exact_level, 2),
    FieldRule("address_1", string_level, 3),
    FieldRule("address_2", string_level, 3),
    FieldRule("suburb", string_level, 3),
    FieldRule("postcode", one_digit_level, 3),
    FieldRule("state", exact_level, 2),
    FieldRule("date_of_birth", date_level, 3),
)


def compare_pairs(left: pd.DataFrame, right: pd.DataFrame, pairs: pd.MultiIndex,
                  rules: tuple[FieldRule, ...] = FIELD_RULES) -> pd.DataFrame:
    """Comparison levels for every pair: one row per pair, one column per field.

    Levels are stored as floats so that a missing comparison can be NaN.
    """
    left_rows = left.loc[pairs.get_level_values(0)]
    right_rows = right.loc[pairs.get_level_values(1)]
    columns: dict[str, np.ndarray] = {}
    for rule in rules:
        values = zip(left_rows[rule.field].to_numpy(), right_rows[rule.field].to_numpy())
        columns[rule.field] = np.array(
            [np.nan if pd.isna(a) or pd.isna(b) else rule.level(a, b) for a, b in values],
            dtype=float,
        )
    return pd.DataFrame(columns, index=pairs)
