"""Comparison levels on hand built pairs."""

import numpy as np
import pandas as pd

from linkage.compare import (AGREE, DISAGREE, PARTIAL, FieldRule, compare_pairs, date_level,
                             exact_level, one_digit_level, string_level)


def test_string_levels():
    assert string_level("michaela", "michaela") == AGREE
    assert string_level("martha", "marhta") == AGREE          # Jaro-Winkler 0.961
    assert string_level("dwayne", "duane") == DISAGREE         # 0.840 is below 0.88
    assert string_level("dixon", "dicksonx") == DISAGREE


def test_exact_and_code_levels():
    assert exact_level("vic", "vic") == 1
    assert exact_level("vic", "nsw") == 0
    assert one_digit_level("3138", "3128") == PARTIAL
    assert one_digit_level("3138", "3183") == DISAGREE
    assert one_digit_level("3138", "3138") == AGREE


def test_date_levels():
    assert date_level("19590905", "19590905") == AGREE
    assert date_level("19590905", "19590906") == PARTIAL      # day differs only
    assert date_level("19590905", "19950905") == PARTIAL      # year differs only
    assert date_level("19590905", "19950906") == DISAGREE


def test_missing_values_give_nan():
    left = pd.DataFrame({"name": ["ann", pd.NA]}, index=["a1", "a2"])
    right = pd.DataFrame({"name": ["ann"]}, index=["b1"])
    pairs = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b1")])
    levels = compare_pairs(left, right, pairs, (FieldRule("name", string_level, 3),))
    assert levels.loc[("a1", "b1"), "name"] == AGREE
    assert np.isnan(levels.loc[("a2", "b1"), "name"])
