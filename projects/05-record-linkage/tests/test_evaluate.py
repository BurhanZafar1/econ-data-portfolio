"""Decision rules and scores on hand built examples."""

import pandas as pd
import pytest

from linkage.evaluate import exact_rule, one_to_one, score_links, threshold_curve


def test_one_to_one_keeps_best_pair_per_record():
    scores = pd.Series([0.9, 0.8, 0.7, 0.6],
                       index=pd.MultiIndex.from_tuples([("a1", "b1"), ("a1", "b2"),
                                                        ("a2", "b1"), ("a2", "b2")]))
    assert list(one_to_one(scores)) == [("a1", "b1"), ("a2", "b2")]


def test_score_by_hand():
    truth = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2"), ("a3", "b3"), ("a4", "b4")])
    predicted = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2"), ("a3", "b4")])
    score = score_links(predicted, truth)
    assert score["true_links_found"] == 2
    assert score["false_links"] == 1
    assert score["missed_links"] == 2
    assert score["precision"] == pytest.approx(2 / 3)
    assert score["recall"] == pytest.approx(0.5)
    assert score["f1"] == pytest.approx(2 * (2 / 3) * 0.5 / (2 / 3 + 0.5))


def test_exact_rule_needs_every_field():
    left = pd.DataFrame({"name": ["ann", "bob"], "dob": ["1", "2"]}, index=["a1", "a2"])
    right = pd.DataFrame({"name": ["ann", "bob"], "dob": ["1", "3"]}, index=["b1", "b2"])
    assert list(exact_rule(left, right, ["name", "dob"])) == [("a1", "b1")]


def test_threshold_curve_by_hand():
    index = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2"), ("a1", "b2")])
    posterior = pd.Series([0.99, 0.6, 0.55], index=index)
    truth = pd.MultiIndex.from_tuples([("a1", "b1"), ("a2", "b2")])
    row = threshold_curve(posterior, truth, [0.5]).iloc[0]
    assert row["links"] == 3
    assert row["precision"] == pytest.approx(2 / 3)
    assert row["model_precision"] == pytest.approx((0.99 + 0.6 + 0.55) / 3)
    assert row["recall"] == 1.0
