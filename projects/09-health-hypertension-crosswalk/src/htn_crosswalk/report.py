"""Figures and markdown tables for the README and the one page summary."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .extract import AGE_LABELS, XW_LABELS  # noqa: E402

SELF_COLOUR = "#eb6834"  # self report
MEASURED_COLOUR = "#2a78d6"  # measured or adjusted
MUTED = "#8a8984"
INK = "#0b0b0b"
SURFACE = "#fcfcfb"


def _style(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9)
    ax.grid(axis="y", color="#e6e5e1", linewidth=0.8)
    ax.set_axisbelow(True)


def figure_gap(table: pd.DataFrame, path: Path) -> None:
    """Self reported versus measured prevalence by age and sex, with sensitivity underneath."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.6), sharex=True, facecolor=SURFACE,
                             gridspec_kw={"height_ratios": [2, 1]})
    x = np.arange(len(XW_LABELS))
    for col, sex in enumerate(("Female", "Male")):
        rows = table[table["sex"] == sex].set_index("xw_group").reindex(XW_LABELS)
        ax = axes[0, col]
        _style(ax)
        ax.plot(x, 100 * rows["p_self"], color=SELF_COLOUR, lw=2, marker="o", ms=7, label="Self report: ever told")
        ax.plot(x, 100 * rows["p_meas"], color=MEASURED_COLOUR, lw=2, marker="s", ms=7,
                label="Measured: 140/90 or on medicine")
        ax.set_title(sex, fontsize=11, color=INK, loc="left")
        ax.set_ylim(0, 80)
        ax.set_ylabel("Prevalence (%)" if col == 0 else "")
        ax2 = axes[1, col]
        _style(ax2)
        ax2.bar(x, 100 * rows["sens"], width=0.55, color=MEASURED_COLOUR, alpha=0.85)
        for xi, s in zip(x, rows["sens"]):
            ax2.text(xi, 100 * s + 3, f"{100 * s:.0f}", ha="center", fontsize=8, color=INK)
        ax2.set_ylim(0, 110)
        ax2.set_ylabel("Sensitivity (%)" if col == 0 else "")
        ax2.set_xticks(x, XW_LABELS)
        ax2.set_xlabel("Age group")
    axes[0, 0].legend(frameon=False, fontsize=9, loc="upper left")
    cycles = table["cycles"].iloc[0]
    fig.suptitle(f"Self report overstates hypertension in young adults and misses it in older adults\n"
                 f"NHANES {cycles}, examined adults, survey weighted. Sensitivity = share of measured cases who report it.",
                 fontsize=10.5, x=0.01, ha="left", color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def figure_validation_and_states(scores: pd.DataFrame, adjusted: pd.DataFrame, year: int, path: Path) -> None:
    """Left: out of sample error by method. Right: BRFSS state values before and after adjustment."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.8), facecolor=SURFACE,
                                      gridspec_kw={"width_ratios": [1, 1.25]})
    _style(left)
    order = scores.iloc[::-1]
    best = scores.loc[scores["key"].str.startswith("crosswalk"), "mae_pp"].idxmin()
    colours = [MEASURED_COLOUR if i == best else MUTED for i in order.index]
    left.barh(np.arange(len(order)), order["mae_pp"], color=colours, height=0.6)
    left.set_yticks(np.arange(len(order)), [_wrap(m) for m in order["method"]], fontsize=8.5)
    for yi, v in enumerate(order["mae_pp"]):
        left.text(v + 0.05, yi, f"{v:.1f}", va="center", fontsize=8.5, color=INK)
    left.set_xlabel("Mean absolute error vs measured (percentage points)")
    left.set_title("Held out error, test cycles 2013-2014 to 2017-2018", fontsize=10, loc="left", color=INK)
    left.grid(axis="y", visible=False)
    left.grid(axis="x", color="#e6e5e1", linewidth=0.8)

    _style(right)
    rows = adjusted[adjusted["year"] == year]
    x = np.arange(len(AGE_LABELS))
    rng = np.random.default_rng(0)  # horizontal jitter only, for legibility
    for i, age in enumerate(AGE_LABELS):
        sub = rows[rows["age_group"] == age]
        jitter = rng.uniform(-0.12, 0.12, len(sub))
        right.scatter(i - 0.18 + jitter, sub["self_report_pct"], s=10, color=SELF_COLOUR, alpha=0.55, lw=0)
        right.scatter(i + 0.18 + jitter, sub["adjusted_pct"], s=10, color=MEASURED_COLOUR, alpha=0.55, lw=0)
        right.hlines(sub["self_report_pct"].median(), i - 0.33, i - 0.03, color=SELF_COLOUR, lw=2.5)
        right.hlines(sub["adjusted_pct"].median(), i + 0.03, i + 0.33, color=MEASURED_COLOUR, lw=2.5)
    right.scatter([], [], color=SELF_COLOUR, label="BRFSS self report")
    right.scatter([], [], color=MEASURED_COLOUR, label="Adjusted to measured")
    right.legend(frameon=False, fontsize=9, loc="upper left")
    right.set_xticks(x, AGE_LABELS)
    right.set_xlabel("Age group")
    right.set_ylabel("Prevalence (%)")
    right.set_title(f"BRFSS {year}: 50 states and DC (dots), median (bar)", fontsize=10, loc="left", color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def _wrap(text: str, width: int = 28) -> str:
    words, lines, line = text.split(), [], ""
    for word in words:
        if len(line) + len(word) + 1 > width and line:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return "\n".join([*lines, line])


def markdown_table(frame: pd.DataFrame) -> str:
    """Plain pipe table (no extra dependency)."""
    header = "| " + " | ".join(frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in frame.itertuples(index=False)]
    return "\n".join([header, rule, *body])
