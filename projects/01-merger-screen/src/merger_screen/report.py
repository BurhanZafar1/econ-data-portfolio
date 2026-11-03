"""Write the results table, the two charts, and the one page manager summary."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to files only, no display needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .concentration import HIGHLY_CONCENTRATED_HHI, SIGNIFICANT_HHI_INCREASE
from .diversion import guppi, proportional_diversion

INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6"]
EXTRA_SERIES = "#8a8984"  # neutral gray for any merger past the fourth (never a new hue)
MAX_GUPPI_LINES = 4
ZONE = "#fbe3da"


def _yes_no(flag: bool) -> str:
    return "Yes" if flag else "No"


def screen_table_markdown(screen: pd.DataFrame) -> str:
    """Human readable version of the screen, rounded the way a memo would show it."""
    header = (
        "| Merger | Type | Combined share (%) | Pre HHI | Change in HHI | Post HHI | "
        "HHI test | 30% share test | Presumed harmful |\n"
        "|---|---|---:|---:|---:|---:|:-:|:-:|:-:|\n"
    )
    lines = [
        f"| {r.parties} | {r.deal_type} | {r.merged_share:.1f} | {r.pre_hhi:,.0f} | {r.delta_hhi:,.1f} | "
        f"{r.post_hhi:,.0f} | {_yes_no(r.hhi_test)} | {_yes_no(r.share_test)} | {_yes_no(r.presumed_illegal)} |"
        for r in screen.itertuples(index=False)
    ]
    return header + "\n".join(lines) + "\n"


def _style_axes(ax: plt.Axes) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_SECONDARY)
    ax.tick_params(colors=INK_SECONDARY)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_hhi_screen(screen: pd.DataFrame, path: Path) -> None:
    """Each merger placed on post merger HHI (x) and change in HHI (y, log scale)."""
    fig, ax = plt.subplots(figsize=(8, 5.2), dpi=150)
    x_max, y_min, y_max = 10_000, 30, 3_000
    ax.fill_between(
        [HIGHLY_CONCENTRATED_HHI, x_max], SIGNIFICANT_HHI_INCREASE, y_max, color=ZONE, zorder=0
    )
    ax.axvline(HIGHLY_CONCENTRATED_HHI, color=INK_SECONDARY, linewidth=1, linestyle="--")
    ax.axhline(SIGNIFICANT_HHI_INCREASE, color=INK_SECONDARY, linewidth=1, linestyle="--")
    ax.text(5_900, 1_800, "Presumed to harm competition\n(post HHI > 1,800 and change > 100)",
            color=INK, fontsize=9, ha="center", va="center")
    for i, row in enumerate(screen.itertuples(index=False)):
        color = SERIES[i] if i < len(SERIES) else EXTRA_SERIES
        ax.scatter(row.post_hhi, row.delta_hhi, s=70, color=color, edgecolor="white", linewidth=1.5, zorder=3)
        ax.annotate(f"{row.parties}\n(change {row.delta_hhi:,.1f})", (row.post_hhi, row.delta_hhi),
                    textcoords="offset points", xytext=(10, -4), fontsize=8.5, color=INK, va="top")
    ax.set_xscale("linear")
    ax.set_yscale("log")
    ax.set_xlim(0, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel("Post merger HHI (0 to 10,000)", color=INK)
    ax.set_ylabel("Change in HHI from the merger (log scale)", color=INK)
    ax.set_title("Where each merger lands against the 2023 Merger Guidelines HHI test",
                 color=INK, fontsize=11, loc="left")
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_guppi_by_margin(shares: pd.DataFrame, mergers: pd.DataFrame, efficiency_credit: float, path: Path) -> None:
    """GUPPI for each direction of the actual deals as the assumed margin varies.

    At most four lines are drawn (two deals, both directions) so the chart stays
    readable; every deal is still in output/diversion_screen.csv.
    """
    margins = np.linspace(0.05, 0.9, 50)
    fig, ax = plt.subplots(figsize=(8, 5.2), dpi=150)
    deals = mergers.loc[mergers["deal_type"] == "actual"]
    if deals.empty:
        deals = mergers
    directions = []
    for merger in deals.itertuples(index=False):
        market = shares.loc[shares["market_id"] == merger.market_id].set_index("firm")["share_pct"]
        for raiser, rival in ((merger.firm_a, merger.firm_b), (merger.firm_b, merger.firm_a)):
            directions.append((raiser, rival, proportional_diversion(market[raiser], market[rival])))
    if len(directions) > MAX_GUPPI_LINES:
        print(f"GUPPI chart shows the first {MAX_GUPPI_LINES} of {len(directions)} directions; see the CSV for all.")
    for color, (raiser, rival, d) in zip(SERIES, directions[:MAX_GUPPI_LINES]):
        ax.plot(margins * 100, guppi(d, margins) * 100, color=color, linewidth=2,
                label=f"{raiser} raises price (D = {d:.1%} to {rival})")
    credit = efficiency_credit * (1 - margins)
    ax.plot(margins * 100, credit * 100, color=INK_SECONDARY, linewidth=1.5, linestyle="--",
            label=f"Efficiency credit E(1 - M), E = {efficiency_credit:.0%}")
    ax.set_xlabel("Assumed price cost margin of both products (%)", color=INK)
    ax.set_ylabel("GUPPI (% of price)", color=INK)
    ax.set_title("Upward pricing pressure under proportional diversion (assumed margins)",
                 color=INK, fontsize=11, loc="left")
    ax.set_xlim(0, 92)
    ax.set_ylim(0, None)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def write_summary(
    screen: pd.DataFrame,
    court: pd.DataFrame,
    diversion: pd.DataFrame,
    path: Path,
    margin: float,
    efficiency_credit: float,
) -> None:
    """One page plain language summary for a manager, written for the bundled court data.

    It names the bundled deals, so run.py only calls it when the default data is used.
    `margin` must be one of the margins in `diversion`."""
    by_id = screen.set_index("merger_id")
    hrb, heinz, hawk, foot = (by_id.loc[k] for k in ("hrb_taxact", "heinz_beechnut", "hrb_taxhawk", "footnote_example"))
    mid = diversion.loc[np.isclose(diversion["assumed_margin"], margin)]
    litigated = mid.loc[mid["merger_id"].isin(["hrb_taxact", "heinz_beechnut"])]
    guppi_range = (litigated["guppi"].min(), litigated["guppi"].max())
    be_range = (litigated["breakeven_margin"].min(), litigated["breakeven_margin"].max())
    hawk_d = mid.loc[mid["price_raised_by"] == "TaxHawk", "diversion_ratio"].iloc[0]
    heinz_court = court.set_index("merger_id").loc["heinz_beechnut"]
    text = f"""# Merger screen: one page summary

**Question.** Would two real mergers that courts later blocked be flagged by the first screen in
the 2023 US Merger Guidelines, and how does the screen behave near its edges? (The courts decided
these cases under older guidelines; this applies today's thresholds to the shares they printed.)

**Answer in one line.** Yes. Both litigated deals clear the presumption thresholds by a wide
margin on the shares printed in the court opinions.

| Deal | Combined share | Post merger HHI | Change in HHI | Flagged? |
|---|---:|---:|---:|:-:|
| H&R Block + TaxACT (2011) | {hrb.merged_share:.1f}% | {hrb.post_hhi:,.0f} | {hrb.delta_hhi:,.0f} | {_yes_no(hrb.presumed_illegal)} |
| Heinz + Beech-Nut (2001) | {heinz.merged_share:.1f}% | {heinz.post_hhi:,.0f} | {heinz.delta_hhi:,.0f} | {_yes_no(heinz.presumed_illegal)} |
| H&R Block + TaxHawk (what if) | {hawk.merged_share:.1f}% | {hawk.post_hhi:,.0f} | {hawk.delta_hhi:,.1f} | {_yes_no(hawk.presumed_illegal)} |
| Court's teaching example | {foot.merged_share:.1f}% | {foot.post_hhi:,.0f} | {foot.delta_hhi:,.0f} | {_yes_no(foot.presumed_illegal)} |

**What the rule says.** A merger is presumed to harm competition if the market ends up with an
HHI above 1,800 and the merger raises it by more than 100 points, or if the merged firm has more
than 30 percent of the market and the HHI rises by more than 100 points. The presumption can be
rebutted with evidence; it starts the conversation, it does not end it.

**Things a manager should know.**
1. The H&R Block numbers are within a few points of the court's (computed post HHI {hrb.post_hhi:,.0f}
   against {court.set_index("merger_id").loc["hrb_taxact", "reported_post_hhi"]:,.0f} in the opinion); the gap is share rounding.
2. For Heinz, the rounded shares in the opinion give a change of {heinz.delta_hhi:,.0f} points
   while the court reported {heinz_court.reported_delta_hhi:,.0f}. The court used share data it did
   not print. Either number is five times the 100 point line, so the conclusion does not move.
3. The screen is a hard line. Buying TaxHawk instead of TaxACT would have raised the HHI by
   {hawk.delta_hhi:.1f} points on the printed shares in a market with an HHI above 4,000, so the
   screen would not flag it. Because those shares are rounded, the true change could be anywhere
   from {hawk.delta_hhi_min_rounding:.1f} to {hawk.delta_hhi_max_rounding:.1f}: the answer turns on
   rounding. Deals near the line deserve a closer look, not a pass.
4. The pricing pressure check (GUPPI, the gross upward pricing pressure index) needs margins that
   are not public. At an assumed {margin:.0%} margin the two litigated deals show GUPPIs between
   {guppi_range[0]:.1%} and {guppi_range[1]:.1%} of price, above the {efficiency_credit * (1 - margin):.0%}
   of price that a {efficiency_credit:.0%} cost saving would offset. Net
   pricing pressure turns positive once margins pass {be_range[0]:.0%} to {be_range[1]:.0%}. Treat
   these as illustrations, not findings.
5. The two screens can disagree. In the TaxHawk what if, the HHI test says no, but TaxHawk's own
   price would face pressure at a {margin:.0%} margin because {hawk_d:.0%} of its lost sales would go
   to H&R Block.

**Limits.** Shares come from court opinions and are rounded. Market definition is taken as given.
Diversion is assumed to follow market shares, which ignores how close the products really are.
"""
    path.write_text(text, encoding="utf-8")
