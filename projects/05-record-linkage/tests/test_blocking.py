"""Blocking on a tiny example where every pair can be listed by hand."""

import pandas as pd
import pytest

from linkage.blocking import BlockingPass, blocking_quality, candidate_pairs, pairs_for_pass

LEFT = pd.DataFrame({"postcode": ["1000", "2000", None], "year": ["1950", "1960", "1970"]},
                    index=pd.Index(["a1", "a2", "a3"], name="rec_id"))
RIGHT = pd.DataFrame({"postcode": ["1000", "1000", "3000"], "year": ["1950", "1970", "1970"]},
                     index=pd.Index(["b1", "b2", "b3"], name="rec_id"))
BY_POSTCODE = BlockingPass("postcode", lambda f: f["postcode"])
BY_YEAR = BlockingPass("year", lambda f: f["year"])


def test_single_pass_skips_missing_keys():
    pairs = pairs_for_pass(LEFT, RIGHT, BY_POSTCODE)
    assert set(pairs) == {("a1", "b1"), ("a1", "b2")}


def test_union_has_no_duplicates():
    pairs = candidate_pairs(LEFT, RIGHT, (BY_POSTCODE, BY_YEAR))
    assert list(pairs) == [("a1", "b1"), ("a1", "b2"), ("a3", "b2"), ("a3", "b3")]


def test_quality_by_hand():
    pairs = candidate_pairs(LEFT, RIGHT, (BY_POSTCODE,))
    links = pd.MultiIndex.from_tuples([("a1", "b1"), ("a3", "b3")])
    quality = blocking_quality(pairs, links, 3, 3)
    assert quality["reduction_ratio"] == pytest.approx(1 - 2 / 9)
    assert quality["pair_completeness"] == pytest.approx(0.5)
