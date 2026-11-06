"""Blocking: compare only record pairs that share at least one cheap key.

Comparing every record in A with every record in B costs |A| x |B| string
comparisons (25 million here). Blocking keeps pairs that agree on at least one
of several keys. A single key misses true pairs whenever that field has a typo,
so several independent passes are combined (Christen 2012, chapter 4).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from .strings import soundex

KeyFunction = Callable[[pd.DataFrame], pd.Series]


@dataclass(frozen=True)
class BlockingPass:
    """One blocking key: a name and a function from records to key values."""

    name: str
    key: KeyFunction


def _soundex_column(frame: pd.DataFrame, column: str) -> pd.Series:
    return frame[column].map(soundex, na_action="ignore")


def _birth_year(frame: pd.DataFrame) -> pd.Series:
    return frame["date_of_birth"].str[:4]


def _concat(*parts: pd.Series) -> pd.Series:
    """Join key parts with '|'; missing if any part is missing."""
    joined = parts[0].astype("string")
    for part in parts[1:]:
        joined = joined + "|" + part.astype("string")
    return joined


DEFAULT_PASSES: tuple[BlockingPass, ...] = (
    BlockingPass("postcode", lambda f: f["postcode"]),
    BlockingPass("surname soundex + birth year",
                 lambda f: _concat(_soundex_column(f, "surname"), _birth_year(f))),
    BlockingPass("given name soundex + birth year",
                 lambda f: _concat(_soundex_column(f, "given_name"), _birth_year(f))),
    BlockingPass("date of birth", lambda f: f["date_of_birth"]),
    BlockingPass("surname soundex + given name soundex",
                 lambda f: _concat(_soundex_column(f, "surname"),
                                   _soundex_column(f, "given_name"))),
)


def pairs_for_pass(left: pd.DataFrame, right: pd.DataFrame,
                   blocking_pass: BlockingPass) -> pd.MultiIndex:
    """Every (A, B) pair whose key values are equal and not missing."""
    keys_left = blocking_pass.key(left).dropna().rename("key").rename_axis("a").reset_index()
    keys_right = blocking_pass.key(right).dropna().rename("key").rename_axis("b").reset_index()
    joined = keys_left.merge(keys_right, on="key")
    return pd.MultiIndex.from_frame(joined[["a", "b"]])


def candidate_pairs(left: pd.DataFrame, right: pd.DataFrame,
                    passes: tuple[BlockingPass, ...] = DEFAULT_PASSES) -> pd.MultiIndex:
    """Union of the pairs from all passes, without duplicates, in sorted order."""
    union = pairs_for_pass(left, right, passes[0])
    for blocking_pass in passes[1:]:
        union = union.union(pairs_for_pass(left, right, blocking_pass))
    return union.sort_values()


def blocking_quality(pairs: pd.MultiIndex, links: pd.MultiIndex,
                     n_left: int, n_right: int) -> dict[str, float]:
    """Reduction ratio and pair completeness (Christen 2012, chapter 7).

    Reduction ratio: share of the full cross product that was skipped.
    Pair completeness: share of true links that survived blocking.
    """
    kept_links = pairs.intersection(links)
    return {
        "candidate_pairs": float(len(pairs)),
        "reduction_ratio": 1 - len(pairs) / (n_left * n_right),
        "pair_completeness": len(kept_links) / len(links),
    }
