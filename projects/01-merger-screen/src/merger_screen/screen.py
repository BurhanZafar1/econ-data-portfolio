"""Run the concentration screen and the diversion screen over a list of mergers."""

from __future__ import annotations

import pandas as pd

from .concentration import (
    delta_hhi,
    delta_hhi_rounding_range,
    fringe_share,
    hhi_bounds,
    structural_presumption,
)
from .diversion import breakeven_margin, guppi, net_upp_per_dollar, proportional_diversion


def _market_shares(shares: pd.DataFrame, market_id: str) -> pd.Series:
    """Shares of the named firms in one market, indexed by firm name."""
    return shares.loc[shares["market_id"] == market_id].set_index("firm")["share_pct"]


def screen_merger(market: pd.Series, firm_a: str, firm_b: str) -> dict[str, float | bool]:
    """Concentration screen for one merger given the named firms' shares in its market."""
    share_a, share_b = float(market[firm_a]), float(market[firm_b])
    pre_low, pre_high = hhi_bounds(market.to_numpy())
    change = delta_hhi(share_a, share_b)
    merged_share = share_a + share_b
    # Judge the presumption on the lower bound: if even the smallest possible HHI
    # crosses the line, the unnamed fringe cannot change the answer.
    result = structural_presumption(pre_low + change, change, merged_share)
    # Also report the answer if the whole fringe were one firm, and the range of the
    # change that rounding of the printed shares allows.
    upper = structural_presumption(pre_high + change, change, merged_share)
    change_min, change_max = delta_hhi_rounding_range(share_a, share_b)
    return {
        "share_a": share_a,
        "share_b": share_b,
        "merged_share": merged_share,
        "fringe_share": fringe_share(market.to_numpy()),
        "pre_hhi": pre_low,
        "pre_hhi_upper": pre_high,
        "delta_hhi": change,
        "delta_hhi_min_rounding": change_min,
        "delta_hhi_max_rounding": change_max,
        "post_hhi": pre_low + change,
        "post_hhi_upper": pre_high + change,
        "hhi_test": result.hhi_test,
        "share_test": result.share_test,
        "presumed_illegal": result.presumed_illegal,
        "presumed_at_upper_bound": upper.presumed_illegal,
    }


def screen_all(shares: pd.DataFrame, mergers: pd.DataFrame) -> pd.DataFrame:
    """One row per merger with shares, HHI levels, and the Guideline 1 flags."""
    rows = []
    for merger in mergers.itertuples(index=False):
        market = _market_shares(shares, merger.market_id)
        rows.append(
            {
                "merger_id": merger.merger_id,
                "deal_type": merger.deal_type,
                "parties": f"{merger.firm_a} + {merger.firm_b}",
                **screen_merger(market, merger.firm_a, merger.firm_b),
            }
        )
    return pd.DataFrame(rows)


def diversion_screen(
    shares: pd.DataFrame,
    mergers: pd.DataFrame,
    margins: tuple[float, ...] = (0.3, 0.5, 0.7),
    aggregate_diversion: float = 1.0,
    efficiency_credit: float = 0.10,
) -> pd.DataFrame:
    """GUPPI and net UPP in both directions for each merger, over a grid of assumed margins.

    Margins and relative prices are not public for these cases, so both parties are
    given the same assumed margin and equal prices. The output is a sensitivity
    table, not an estimate of any firm's actual pricing incentive.
    """
    rows = []
    for merger in mergers.itertuples(index=False):
        market = _market_shares(shares, merger.market_id)
        for raiser, rival in ((merger.firm_a, merger.firm_b), (merger.firm_b, merger.firm_a)):
            diversion = proportional_diversion(market[raiser], market[rival], aggregate_diversion)
            for margin in margins:
                rows.append(
                    {
                        "merger_id": merger.merger_id,
                        "price_raised_by": raiser,
                        "sales_diverted_to": rival,
                        "diversion_ratio": diversion,
                        "breakeven_margin": breakeven_margin(diversion, efficiency_credit),
                        "assumed_margin": margin,
                        "guppi": guppi(diversion, margin),
                        "net_upp_per_dollar": net_upp_per_dollar(diversion, margin, margin, efficiency_credit),
                    }
                )
    return pd.DataFrame(rows)


def compare_with_court(screen: pd.DataFrame, reported: pd.DataFrame) -> pd.DataFrame:
    """Put the computed HHI figures next to the figures printed in each opinion."""
    merged = screen.merge(reported, on="merger_id", how="inner")
    return merged[
        [
            "merger_id",
            "pre_hhi",
            "reported_pre_hhi",
            "delta_hhi",
            "reported_delta_hhi",
            "post_hhi",
            "reported_post_hhi",
            "merged_share",
            "reported_merged_share",
            "citation",
        ]
    ]
