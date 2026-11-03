"""Load and validate the market share and merger input files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SHARE_COLUMNS = {"market_id", "market", "firm", "share_pct"}
MERGER_COLUMNS = {"merger_id", "market_id", "firm_a", "firm_b", "deal_type", "description"}
# Shares quoted in court opinions are rounded, so allow a little slack above 100.
SHARE_SUM_TOLERANCE = 0.5
DEAL_TYPES = {"actual", "hypothetical", "worked example"}


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing columns: {sorted(missing)}")


def validate_shares(shares: pd.DataFrame) -> None:
    """Raise ValueError if shares are out of range, duplicated, or sum above 100."""
    _require_columns(shares, SHARE_COLUMNS, "market share file")
    if shares["share_pct"].isna().any():
        raise ValueError("market share file has blank shares")
    if ((shares["share_pct"] < 0) | (shares["share_pct"] > 100)).any():
        raise ValueError("every share must be between 0 and 100 percent")
    if shares.duplicated(["market_id", "firm"]).any():
        raise ValueError("a firm appears twice in the same market")
    totals = shares.groupby("market_id")["share_pct"].sum()
    too_big = totals[totals > 100 + SHARE_SUM_TOLERANCE]
    if not too_big.empty:
        raise ValueError(f"shares sum above 100 in markets: {list(too_big.index)}")


def validate_mergers(mergers: pd.DataFrame, shares: pd.DataFrame) -> None:
    """Raise ValueError if a merger names a market or firm that is not in the share file."""
    _require_columns(mergers, MERGER_COLUMNS, "merger file")
    known = set(zip(shares["market_id"], shares["firm"]))
    for row in mergers.itertuples(index=False):
        for firm in (row.firm_a, row.firm_b):
            if (row.market_id, firm) not in known:
                raise ValueError(f"{row.merger_id}: firm '{firm}' not found in market '{row.market_id}'")
        if row.deal_type not in DEAL_TYPES:
            raise ValueError(f"{row.merger_id}: deal_type must be one of {sorted(DEAL_TYPES)}")
        if row.firm_a == row.firm_b:
            raise ValueError(f"{row.merger_id}: a firm cannot merge with itself")


def load_inputs(shares_path: Path, mergers_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read both CSV files and check them before any calculation runs."""
    shares = pd.read_csv(shares_path)
    mergers = pd.read_csv(mergers_path)
    validate_shares(shares)
    validate_mergers(mergers, shares)
    return shares, mergers
