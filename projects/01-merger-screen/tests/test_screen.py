"""End to end checks against figures printed in the court opinions."""

from pathlib import Path

import pandas as pd
import pytest

from merger_screen.data import load_inputs, validate_shares
from merger_screen.screen import diversion_screen, screen_all

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def screen():
    shares, mergers = load_inputs(DATA / "market_shares.csv", DATA / "mergers.csv")
    return screen_all(shares, mergers).set_index("merger_id")


def test_hrb_matches_court(screen):
    # United States v. H&R Block (D.D.C. 2011): pre HHI 4,291, change about 400,
    # post HHI 4,691, combined share 28.4 percent. Shares are rounded, so allow a few points.
    row = screen.loc["hrb_taxact"]
    assert row.pre_hhi == pytest.approx(4291, abs=5)
    assert row.delta_hhi == pytest.approx(400, abs=1)
    assert row.post_hhi == pytest.approx(4691, abs=5)
    assert row.merged_share == pytest.approx(28.4)
    assert row.presumed_illegal


def test_heinz_flagged_and_close_to_court(screen):
    # FTC v. H.J. Heinz (D.C. Cir. 2001): pre HHI 4,775, change 510. The printed shares give
    # 4,765 and 536; the gap comes from the court using share data it did not print.
    row = screen.loc["heinz_beechnut"]
    assert row.pre_hhi == pytest.approx(4775, rel=0.01)
    assert row.delta_hhi == pytest.approx(2 * 17.4 * 15.4)
    assert row.hhi_test and row.share_test


def test_footnote_example_exact(screen):
    row = screen.loc["footnote_example"]
    assert row.pre_hhi == pytest.approx(1304)
    assert row.delta_hhi == pytest.approx(130)
    assert not row.presumed_illegal


def test_taxhawk_just_misses(screen):
    row = screen.loc["hrb_taxhawk"]
    assert row.delta_hhi == pytest.approx(99.84)
    assert not row.presumed_illegal


def test_post_minus_pre_equals_delta(screen):
    assert (screen.post_hhi - screen.pre_hhi - screen.delta_hhi).abs().max() < 1e-9
    assert (screen.pre_hhi_upper >= screen.pre_hhi).all()


def test_diversion_screen_shape():
    shares, mergers = load_inputs(DATA / "market_shares.csv", DATA / "mergers.csv")
    table = diversion_screen(shares, mergers, margins=(0.4, 0.6))
    assert len(table) == len(mergers) * 2 * 2
    assert table["guppi"].between(0, 1).all()


def test_bad_shares_rejected():
    bad = pd.DataFrame({"market_id": ["m", "m"], "market": ["x", "x"], "firm": ["a", "b"], "share_pct": [70, 40]})
    with pytest.raises(ValueError):
        validate_shares(bad)


def test_readme_table_matches_fresh_run():
    # Every row of the README results table must be reproduced by the code.
    from merger_screen.report import screen_table_markdown

    shares, mergers = load_inputs(DATA / "market_shares.csv", DATA / "mergers.csv")
    table = screen_table_markdown(screen_all(shares, mergers))
    readme = (DATA.parent / "README.md").read_text(encoding="utf-8")
    for line in table.strip().splitlines():
        assert line in readme


def test_upper_bound_flag_never_weaker(screen):
    # A larger fringe firm can only raise the HHI, so it can add flags but never remove them.
    assert (screen.presumed_at_upper_bound | ~screen.presumed_illegal).all()


def test_unknown_deal_type_rejected():
    shares, mergers = load_inputs(DATA / "market_shares.csv", DATA / "mergers.csv")
    bad = mergers.assign(deal_type="rumour")
    from merger_screen.data import validate_mergers

    with pytest.raises(ValueError):
        validate_mergers(bad, shares)
