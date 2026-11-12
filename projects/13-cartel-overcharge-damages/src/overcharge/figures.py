"""The two charts in output/."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ACTUAL = "#2a78d6"
BUT_FOR = "#eb6834"
WAR_SHADE = "#d9d8d4"
INK = "#0b0b0b"
MUTED = "#52514e"
FIRST_YEAR = 1880


def _style(ax: plt.Axes) -> None:
    """Recessive axes: no top or right spine, light horizontal grid."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED)
    ax.grid(axis="y", color="#e6e5e1", linewidth=0.8)
    ax.set_axisbelow(True)


def price_chart(df: pd.DataFrame, but_for: pd.Series, b: float, path: Path) -> None:
    """Weekly grain rate with price war weeks shaded and the two but for prices."""
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
    _style(ax)
    years = FIRST_YEAR + (df["week"] - 1) / 52.0
    for _, spell in df[df["cartel"] == 0].groupby("episode"):
        start = FIRST_YEAR + (spell["week"].min() - 1.5) / 52.0
        end = FIRST_YEAR + (spell["week"].max() - 0.5) / 52.0
        ax.axvspan(start, end, color=WAR_SHADE, linewidth=0, zorder=0)
    ax.plot(years, df["price"], color=ACTUAL, linewidth=2, label="Actual rate")
    cartel = df["cartel"] == 1
    dummy_but_for = df["price"].where(cartel) * np.exp(-b)
    ax.plot(years, dummy_but_for, color=BUT_FOR, linewidth=1.6,
            label="But for rate, dummy variable method")
    ax.plot(years[cartel], but_for, color=BUT_FOR, linewidth=0, marker="o",
            markersize=3, alpha=0.6, label="But for rate, forecasting method")
    ax.set_ylabel("Grain rate, dollars per 100 lbs", color=INK)
    ax.set_ylim(0, 0.45)
    ax.set_xlim(FIRST_YEAR, FIRST_YEAR + df["week"].max() / 52.0)
    ax.set_title("Grain rate under the JEC cartel, 1880 to 1886 (grey bands: price wars)",
                 loc="left", color=INK, fontsize=12)
    ax.legend(frameon=False, loc="lower left", fontsize=9)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def estimates_chart(table: pd.DataFrame, path: Path) -> None:
    """Overcharge (percent above the but for price) by method, with 95% intervals."""
    rows = table.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=150)
    _style(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color="#e6e5e1", linewidth=0.8)
    y = np.arange(len(rows))
    pct = 100 * rows["overcharge_pct_of_but_for"]
    has_ci = rows["hac_se"].notna()
    low = 100 * (np.exp(rows["log_overcharge_b"] - 1.96 * rows["hac_se"]) - 1)
    high = 100 * (np.exp(rows["log_overcharge_b"] + 1.96 * rows["hac_se"]) - 1)
    ax.hlines(y[has_ci], low[has_ci], high[has_ci], color=ACTUAL, linewidth=2)
    colors = [ACTUAL if ci else BUT_FOR for ci in has_ci]
    ax.scatter(pct, y, color=colors, s=50, zorder=3, edgecolor="white", linewidth=1.5)
    for yi, value in zip(y, pct):
        ax.text(value, yi + 0.28, f"{value:.0f}%", ha="center", fontsize=8, color=MUTED)
    ax.set_yticks(y, rows["method"], fontsize=8.5, color=INK)
    ax.set_xlim(0, 75)
    ax.set_xlabel("Overcharge, percent above the but for price (lines: 95% HAC intervals)",
                  color=INK)
    ax.set_title(f"Every method finds an overcharge between {pct.min():.0f}% and {pct.max():.0f}%",
                 loc="left", color=INK, fontsize=12)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
