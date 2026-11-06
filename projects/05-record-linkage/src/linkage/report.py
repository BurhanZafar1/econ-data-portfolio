"""Charts and markdown tables written to output/."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

TRUE_COLOR = "#2a78d6"
FALSE_COLOR = "#eb6834"
INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"


def _style(axis: plt.Axes) -> None:
    axis.set_facecolor(SURFACE)
    axis.grid(axis="y", color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color(MUTED)
    axis.tick_params(colors=MUTED)


def weight_histogram(weights: pd.Series, is_true: np.ndarray, cutoff: float, path: Path) -> None:
    """Distribution of match weights for true and false candidate pairs."""
    bins = np.arange(np.floor(weights.min()), np.ceil(weights.max()) + 1, 1.0)
    figure, axis = plt.subplots(figsize=(8, 4.5), dpi=150, facecolor=SURFACE)
    axis.hist(weights[~is_true], bins=bins, color=FALSE_COLOR, label="Different people",
              edgecolor=SURFACE, linewidth=1)
    axis.hist(weights[is_true], bins=bins, color=TRUE_COLOR, label="Same person",
              edgecolor=SURFACE, linewidth=1, alpha=0.9)
    axis.axvline(cutoff, color=INK, linewidth=1.5, linestyle="--")
    axis.annotate("link above this line\n(posterior 0.5)", xy=(cutoff, 0.9),
                  xycoords=("data", "axes fraction"), xytext=(6, 0), textcoords="offset points",
                  color=INK, fontsize=9, va="top")
    axis.set_yscale("log")
    axis.set_xlabel("Fellegi-Sunter match weight (bits of evidence)", color=INK)
    axis.set_ylabel("Candidate pairs (log scale)", color=INK)
    axis.set_title("The model separates matches from non-matches without any labels",
                   color=INK, loc="left", fontsize=11)
    _style(axis)
    axis.legend(frameon=False, loc="upper right")
    figure.tight_layout()
    figure.savefig(path, facecolor=SURFACE)
    plt.close(figure)


def method_chart(table: pd.DataFrame, path: Path) -> None:
    """True links found and false links made, by method."""
    figure, axis = plt.subplots(figsize=(9, 5), dpi=150, facecolor=SURFACE)
    positions = np.arange(len(table))
    height = 0.38
    axis.barh(positions - height / 2, table["true_links_found"], height=height,
              color=TRUE_COLOR, label="True links found")
    axis.barh(positions + height / 2, table["false_links"], height=height,
              color=FALSE_COLOR, label="False links made")
    for y, (found, false) in enumerate(zip(table["true_links_found"], table["false_links"])):
        axis.text(found + 40, y - height / 2, f"{found:,}", va="center", color=INK, fontsize=9)
        axis.text(false + 40, y + height / 2, f"{false:,}", va="center", color=INK, fontsize=9)
    axis.set_yticks(positions, table["method"], color=INK)
    axis.invert_yaxis()
    axis.axvline(table["true_links_total"].iloc[0], color=MUTED, linewidth=1, linestyle=":")
    axis.set_xlim(0, table["true_links_total"].iloc[0] * 1.15)
    axis.set_xlabel("Record pairs (5,000 true links exist)", color=INK)
    axis.set_title("Exact merging finds fewer than half the true links",
                   color=INK, loc="left", fontsize=11, pad=24)
    _style(axis)
    axis.grid(axis="y", visible=False)
    axis.grid(axis="x", color=GRID, linewidth=0.8)
    axis.xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    axis.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 1.0), ncol=2)
    figure.tight_layout()
    figure.savefig(path, facecolor=SURFACE)
    plt.close(figure)


def markdown_table(frame: pd.DataFrame, decimals: int = 4) -> str:
    """A pipe table with floats rounded and integers comma grouped."""
    def cell(value: object) -> str:
        if isinstance(value, (int, np.integer)):
            return f"{value:,}"
        if isinstance(value, (float, np.floating)):
            return f"{value:.{decimals}f}"
        return str(value)

    header = "| " + " | ".join(frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    body = ["| " + " | ".join(cell(v) for v in row) + " |" for row in frame.itertuples(index=False)]
    return "\n".join([header, rule, *body]) + "\n"
