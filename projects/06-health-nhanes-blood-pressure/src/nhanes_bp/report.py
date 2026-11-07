"""Figures and markdown tables for the README and the one page summary."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def _style(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)


def _band(ax: plt.Axes, rows: pd.DataFrame, color: str, label: str, dashed: bool = False) -> None:
    x = range(len(rows))
    ax.fill_between(x, rows["lower95"], rows["upper95"], color=color, alpha=0.15, linewidth=0)
    ax.plot(x, rows["estimate"], color=color, linewidth=2, linestyle="--" if dashed else "-",
            marker="o", markersize=5, label=label)


def plot_trends(table: pd.DataFrame, path: Path) -> None:
    """Two panels: hypertension crude vs age standardized; standardized mean SBP by sex."""
    cycles = sorted(table["cycle"].unique())
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))

    ax = axes[0]
    for kind, color, label, dashed in (
        ("age_standardized", BLUE, "Age standardized (WHO 2000-2025 standard)", False),
        ("crude", ORANGE, "Crude (actual US age mix)", True),
    ):
        rows = table.query("measure == 'htn140' and sex == 'Both' and type == @kind").sort_values("cycle")
        _band(ax, rows, color, label, dashed)
    ax.set_title("Hypertension prevalence, adults 20+\n(SBP ≥140 or DBP ≥90 mmHg, or on medication)",
                 fontsize=11, color=INK, loc="left")
    ax.set_ylabel("Percent of adults", color=MUTED)

    ax = axes[1]
    for sex, color in (("Male", BLUE), ("Female", ORANGE)):
        rows = table.query("measure == 'sbp' and sex == @sex and type == 'age_standardized'").sort_values("cycle")
        _band(ax, rows, color, "Men" if sex == "Male" else "Women")
    ax.set_title("Age standardized mean systolic blood pressure, adults 20+",
                 fontsize=11, color=INK, loc="left")
    ax.set_ylabel("mmHg", color=MUTED)

    for ax in axes:
        _style(ax)
        ax.set_xticks(range(len(cycles)))
        ax.set_xticklabels([c.replace("-", "–\n") for c in cycles], fontsize=8)
        ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.text(0.01, 0.01, "Source: CDC NHANES 1999–2018 examination files. Shaded bands are design based 95% "
             "confidence intervals.", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_validation(compare: pd.DataFrame, path: Path) -> None:
    """Our estimates against NCHS Data Brief 364, with published ±1.96 SE bars."""
    rows = compare[compare["sex"] == "Both"].sort_values("cycle")
    x = range(len(rows))
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.errorbar(x, rows["published"], yerr=1.96 * rows["published_se"], fmt="s", color=ORANGE,
                markersize=11, markerfacecolor="none", markeredgewidth=1.5, capsize=3, linewidth=1.5, label="NCHS Data Brief 364 (published, ±1.96 SE)")
    ax.plot(x, rows["ours"], "o", color=BLUE, markersize=5, zorder=3, label="This project")
    ax.set_xticks(list(x))
    ax.set_xticklabels([c.replace("-", "–\n") for c in rows["cycle"]], fontsize=8)
    ax.set_ylabel("Age adjusted percent", color=MUTED)
    ax.set_title("Validation: hypertension (≥130/80 or medication), adults 18+, US 2000 standard",
                 fontsize=11, color=INK, loc="left")
    _style(ax)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fmt_ci(row: pd.Series, digits: int = 1) -> str:
    return f"{row['estimate']:.{digits}f} ({row['lower95']:.{digits}f} to {row['upper95']:.{digits}f})"


def headline_table(table: pd.DataFrame, first: str, last: str) -> pd.DataFrame:
    """Rows: measure and sex. Columns: first and last cycle, crude and age standardized."""
    labels = {"htn140": "Hypertension ≥140/90 or meds (%)", "htn130": "Hypertension ≥130/80 or meds (%)",
              "sbp": "Mean SBP (mmHg)"}
    sex_names = {"Both": "All adults", "Male": "Men", "Female": "Women"}
    records = []
    for measure in ("htn140", "htn130", "sbp"):
        for sex in ("Both", "Male", "Female"):
            rec = {"Indicator": labels[measure], "Group": sex_names[sex]}
            for cycle in (first, last):
                for kind, tag in (("crude", "crude"), ("age_standardized", "age std.")):
                    row = table.query("measure == @measure and sex == @sex and type == @kind and cycle == @cycle")
                    rec[f"{cycle} {tag}"] = fmt_ci(row.iloc[0])
            records.append(rec)
    return pd.DataFrame(records)


def to_markdown(frame: pd.DataFrame) -> str:
    """Plain pipe table without needing the tabulate package."""
    header = "| " + " | ".join(frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in frame.itertuples(index=False)]
    return "\n".join([header, rule, *body]) + "\n"
