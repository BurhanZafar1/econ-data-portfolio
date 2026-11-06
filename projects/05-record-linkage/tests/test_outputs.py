"""The full pipeline: totals add up, signs make sense, committed outputs reproduce."""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fresh_run():
    subprocess.run([sys.executable, str(ROOT / "run.py")], check=True, capture_output=True)
    return {
        "headline": json.loads((ROOT / "output" / "headline.json").read_text()),
        "methods": pd.read_csv(ROOT / "output" / "method_comparison.csv"),
        "params": pd.read_csv(ROOT / "output" / "m_u_parameters.csv"),
        "blocking": pd.read_csv(ROOT / "output" / "blocking_passes.csv"),
    }


def test_counts_add_up(fresh_run):
    methods = fresh_run["methods"]
    assert (methods["true_links_found"] + methods["missed_links"] == 5000).all()
    assert (methods["true_links_found"] + methods["false_links"] == methods["links"]).all()


def test_blocking_is_monotone(fresh_run):
    blocking = fresh_run["blocking"]
    assert blocking["pairs_cumulative"].is_monotonic_increasing
    assert blocking["completeness_cumulative"].is_monotonic_increasing
    assert blocking["completeness_cumulative"].iloc[-1] == pytest.approx(
        fresh_run["headline"]["pair_completeness"])


def test_agreement_is_evidence_for_a_match(fresh_run):
    params = fresh_run["params"]
    top = params.loc[params.groupby("field")["level"].idxmax()].set_index("field")
    bottom = params[params["level"] == 0].set_index("field")
    # Disagreeing is always evidence against; agreeing is evidence for, except
    # postcode, whose agreement is diluted because blocking used it as a key.
    assert (bottom["weight_bits"] < 0).all()
    assert (top.drop(index="postcode")["weight_bits"] > 0).all()
    assert (params.groupby("field")[["m", "u"]].sum().round(9) == 1).all().all()


def test_headline_numbers(fresh_run):
    headline = fresh_run["headline"]
    assert headline["candidate_pairs"] == 33_263
    assert headline["true_matches_in_candidates"] == 4_981
    methods = fresh_run["methods"].set_index("method")
    assert methods.loc["Exact merge on name and birth date", "true_links_found"] == 2_079
    assert methods.loc["Fellegi-Sunter, all fields, one to one", "true_links_found"] == 4_974
    assert methods.loc["Fellegi-Sunter, all fields, one to one", "false_links"] == 0
