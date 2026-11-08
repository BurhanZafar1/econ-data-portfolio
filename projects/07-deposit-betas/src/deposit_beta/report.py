"""Charts and the headline table."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .cycles import CYCLES, beta_path  # noqa: E402
from .data import ERA_2021, PRODUCT_LABELS, PRODUCTS  # noqa: E402

# Fixed categorical order, one color per product everywhere; the funds rate is ink.
COLORS = {"checking": "#2a78d6", "savings": "#eb6834", "money_market": "#1baf7a", "cd_12m": "#eda100"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def _style(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)


def plot_rates(panel: pd.DataFrame, path: Path) -> None:
    """Funds rate and the four national deposit rates, with the FDIC method break marked."""
    dates = panel.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    ax.plot(dates, panel["fedfunds"], color=INK, linewidth=2, label="Federal funds rate")
    for product in PRODUCTS:
        for era, rows in panel.groupby("era"):
            ax.plot(
                rows.index.to_timestamp(),
                rows[product],
                color=COLORS[product],
                linewidth=2,
                label=PRODUCT_LABELS[product] if era == ERA_2021 else None,
            )
    first_new = panel.index[panel["era"] == ERA_2021][0].to_timestamp()
    ax.axvline(first_new, color=MUTED, linestyle=":", linewidth=1)
    ax.text(first_new, 5.55, " FDIC method change (Apr 2021)", color=MUTED, fontsize=8, va="top")
    last = panel.iloc[-1]
    for product in PRODUCTS:
        ax.annotate(
            PRODUCT_LABELS[product], (dates[-1], last[product]), xytext=(4, 0),
            textcoords="offset points", fontsize=8, color=INK, va="center",
        )
    _style(ax)
    ax.set_ylabel("Percent per year", color=MUTED)
    ax.set_ylim(0, 5.7)
    ax.set_title("Deposit rates barely followed the Fed (FDIC national averages, monthly)", loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0, 0.93))
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_beta_paths(panel: pd.DataFrame, path: Path) -> None:
    """Cumulative beta by months since the cycle began: 2022 hikes and 2024 cuts."""
    chosen = [c for c in CYCLES if c.name in ("2022-2023 hikes", "2024-2025 cuts")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), dpi=150, sharey=True)
    for ax, cycle in zip(axes, chosen):
        for product in PRODUCTS:
            series = beta_path(panel, product, cycle.base, cycle.end)
            months = range(len(series))
            ax.plot(months, series.to_numpy(), color=COLORS[product], linewidth=2, label=PRODUCT_LABELS[product])
        _style(ax)
        ax.set_title(f"{cycle.name} (from {cycle.base})", loc="left", fontsize=10)
        ax.set_xlabel("Months since the cycle began", color=MUTED)
        ax.axhline(0, color=MUTED, linewidth=0.8)
    axes[0].set_ylabel("Cumulative beta (deposit change / funds change)", color=MUTED)
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Pass-through builds slowly on the way up and stays small on the way down", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def headline_table(cycles: pd.DataFrame, pass_through: pd.DataFrame) -> str:
    """Markdown table: cycle betas by product, then regression long run betas."""
    wide = cycles.pivot(index="product", columns="cycle", values="beta").reindex(list(PRODUCTS))
    wide = wide[[c.name for c in CYCLES]]
    main = pass_through.set_index("product")
    header = "| Product | " + " | ".join(wide.columns) + " | Regression up beta (SE) | Regression down beta (SE) |"
    lines = [header, "|" + "---|" * (len(wide.columns) + 3)]
    for product, row in wide.iterrows():
        fit = main.loc[product]
        cells = " | ".join(f"{v:.3f}" for v in row)
        lines.append(
            f"| {PRODUCT_LABELS[product]} | {cells} | {fit.beta_up:.3f} ({fit.se_up:.3f}) | "
            f"{fit.beta_down:.3f} ({fit.se_down:.3f}) |"
        )
    return "\n".join(lines) + "\n"
