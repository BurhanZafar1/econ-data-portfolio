"""Known answer test on real data: reproduce NCHS Data Brief 364, Figure 4.

Thirty published age adjusted hypertension percents (10 cycles x total, men,
women) and the published 2017-2018 sample size of 5,199.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nhanes_bp.estimates import add_indicators  # noqa: E402
from run import validate_against_nchs  # noqa: E402


@pytest.fixture(scope="module")
def comparison() -> pd.DataFrame:
    frame = add_indicators(pd.read_csv(ROOT / "data" / "nhanes_bp_extract.csv.gz"))
    return validate_against_nchs(frame)


def test_all_thirty_published_estimates_reproduced_to_rounding(comparison):
    assert len(comparison) == 30
    # Published values are rounded to 0.1, so 0.1 points is the tightest fair bar.
    assert comparison["difference"].abs().max() < 0.1


def test_standard_errors_match_published(comparison):
    assert (comparison["ours_se"] - comparison["published_se"]).abs().max() < 0.1


def test_published_sample_size_2017_2018(comparison):
    row = comparison.query("cycle == '2017-2018' and sex == 'Both'").iloc[0]
    assert row["n"] == 5199
