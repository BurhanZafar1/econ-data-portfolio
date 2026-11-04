"""Tables, charts and the manager summary."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from staggered_did import bacon  # noqa: E402

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e6e4dd"
TYPE_STYLE = {
    bacon.TREATED_VS_UNTREATED: (BLUE, "o"),
    bacon.EARLY_VS_LATE: (ORANGE, "s"),
    bacon.LATE_VS_EARLY: (AQUA, "^"),
}


def _style_axes(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(MUTED)
    ax.tick_params(colors=MUTED)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_event_study(
    table: pd.DataFrame, placebo: pd.DataFrame, group: int, path: Path
) -> None:
    """Event study with joint bands, TWFE leads and lags, and Illinois placebos.

    From event time 2 on, one state is treated, so a cluster band is not
    credible. Those points show the range of placebo state estimates instead.
    """
    fig, ax = plt.subplots(figsize=(8.6, 4.8), dpi=200)
    _style_axes(ax)
    ax.axhline(0, color=INK, linewidth=0.9)
    ax.axvline(-0.5, color=MUTED, linewidth=0.9, linestyle=":")
    ax.plot(-1, 0, "o", color=INK, markersize=4)
    ax.annotate(
        "Reference year", (-1, 0), textcoords="offset points", xytext=(0, 8),
        ha="center", color=MUTED, fontsize=8,
    )

    reliable = table[table["treated_states"] > 1]
    single = table[table["treated_states"] == 1]
    ax.errorbar(
        reliable["event_time"] - 0.07,
        reliable["estimate"],
        yerr=[
            reliable["estimate"] - reliable["band_low"],
            reliable["band_high"] - reliable["estimate"],
        ],
        fmt="o", color=BLUE, markersize=6, linewidth=1.6, capsize=0,
        label="Callaway and Sant'Anna, 95% joint band (state clustered)",
    )
    placebo_by_year = placebo.set_index("year")
    lows, highs = [], []
    for e in single["event_time"]:
        row = placebo_by_year.loc[group + int(e)]
        lows.append(row["placebo_q05"])
        highs.append(row["placebo_q95"])
    ax.vlines(
        single["event_time"] - 0.07, lows, highs,
        color=MUTED, linewidth=5, alpha=0.3,
        label="Illinois only: 5th to 95th percentile of placebo states",
    )
    ax.plot(
        single["event_time"] - 0.07, single["estimate"], "o",
        markerfacecolor="white", markeredgecolor=BLUE, markeredgewidth=1.6,
        markersize=6, linestyle="none", label="Callaway and Sant'Anna, Illinois only",
    )
    ax.plot(
        table["event_time"] + 0.07, table["twfe_estimate"], "D",
        color=ORANGE, markersize=5, linestyle="none", label="TWFE leads and lags",
    )
    ax.set_xlabel("Years since the state raised its minimum wage", color=INK)
    ax.set_ylabel("Effect on log teen employment", color=INK)
    ax.set_title(
        "Effects look large after two years, but only one state is observed that long",
        loc="left", color=INK, fontsize=11,
    )
    ax.set_xticks(sorted({*table["event_time"], -1}))
    ax.legend(frameon=False, fontsize=8, loc="lower left", labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_bacon(table: pd.DataFrame, twfe_estimate: float, path: Path) -> None:
    """Scatter of 2x2 estimates against their weight in the TWFE coefficient."""
    fig, ax = plt.subplots(figsize=(8.6, 4.4), dpi=200)
    _style_axes(ax)
    ax.axhline(0, color=INK, linewidth=0.9)
    ax.axhline(twfe_estimate, color=MUTED, linewidth=1.2, linestyle="--")
    ax.annotate(
        f"TWFE estimate {twfe_estimate:.4f}",
        (0.30, twfe_estimate), xytext=(0, 5), textcoords="offset points",
        color=MUTED, fontsize=8,
    )
    for kind, (color, marker) in TYPE_STYLE.items():
        rows = table[table["type"] == kind]
        ax.scatter(
            rows["weight"], rows["estimate"], s=46, color=color, marker=marker,
            edgecolors="white", linewidths=1, label=kind, zorder=3,
        )
    for row in table.nlargest(3, "weight").itertuples():
        ax.annotate(
            f"{row.treated} vs {row.control.lower()}", (row.weight, row.estimate),
            textcoords="offset points", xytext=(0, -15), ha="center",
            color=INK, fontsize=8,
        )
    ax.set_xlim(left=-0.02, right=0.6)
    ax.set_xlabel("Weight in the TWFE coefficient", color=INK)
    ax.set_ylabel("2x2 DiD estimate", color=INK)
    ax.set_title(
        "Most of the TWFE weight comes from clean comparisons with untreated states",
        loc="left", color=INK, fontsize=11,
    )
    ax.legend(frameon=False, fontsize=8, loc="upper right", labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _fmt(value: float) -> str:
    return "n/a" if pd.isna(value) else f"{value:.4f}"


def estimates_markdown(table: pd.DataFrame) -> str:
    """The main results table as Markdown."""
    lines = [
        "| Estimator | Estimate | County SE | State SE |",
        "|---|---:|---:|---:|",
    ]
    for row in table.itertuples():
        lines.append(
            f"| {row.estimator} | {_fmt(row.estimate)} | {_fmt(row.se_county)} "
            f"| {_fmt(row.se_state)} |"
        )
    return "\n".join(lines) + "\n"


def write_summary(path: Path, facts: dict[str, float]) -> None:
    """One page for a manager with no econometrics background."""
    text = f"""# Summary: did state minimum wage increases reduce teen employment?

**Question.** States raised their minimum wages in different years. The standard
regression for this design can give a misleading answer when effects change over
time. We rebuilt the estimate with a method designed for staggered rollouts and
checked how far the evidence can be pushed.

**Data.** 500 US counties in 29 states, 2003 to 2007, from the public sample
that accompanies the Callaway and Sant'Anna paper. It is a teaching subset, so
treat the numbers as an illustration, not a policy finding.

**Headline.** The preferred estimate is a teen employment decline of about
{abs(facts["group_overall"]) * 100:.1f} percent in treated counties. Using all earlier
years as the baseline instead of only the last one gives
{abs(facts["long_difference"]) * 100:.1f} percent. The standard regression gives
{abs(facts["twfe"]) * 100:.1f} percent, so here it was not badly wrong. Only
{facts["already_treated_weight"] * 100:.0f} percent of its weight comes from the
problem comparison, where already treated states act as controls.

**What to be careful about.**

- The large event study average ({abs(facts["dynamic_overall"]) * 100:.1f} percent)
  leans on years 2 and 3 after treatment, and only Illinois is observed that long.
  Using the same cohorts in years 0 and 1, the average is
  {abs(facts["balanced_overall"]) * 100:.1f} percent.
- Illinois alone cannot carry the claim. {facts["illinois_as_extreme"]:.0f} of
  {facts["illinois_placebos"]:.0f} untreated states show a gap as large as its
  average change, for a placebo p value of {facts["illinois_p"]:.2f}.
- Statistical support is borderline. Reassigning the policy at random across states
  gives a p value of {facts["randomization_p"]:.2f} for the preferred estimate. With
  errors clustered by state, the level at which policy changed, the standard
  regression has a t statistic of only {abs(facts["twfe_t"]):.1f}.
- Treated states dipped in the year before their increase, by
  {abs(facts["lead_one"]) * 100:.1f} percent on average. The formal pre test does
  not reject parallel trends, but a test on so few years has limited power. That dip
  is why the choice of baseline moves the estimate.

**Bottom line.** The data lean toward a small negative effect of about 3 to 4 percent,
with borderline statistical support. They cannot say whether losses keep growing past
the first year after a wage increase, because only one state is observed that long.
Any decision should rest on the full county sample and more years of data.
"""
    path.write_text(text, encoding="utf-8")
