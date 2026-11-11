"""Tables and charts written to output/."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from sbp_paf import AGE_LABELS, SEXES  # noqa: E402
from sbp_paf.risks import TMREL_HIGH, TMREL_LOW  # noqa: E402

COLORS = {"Male": "#2b6cb0", "Female": "#c05621"}


def pct(x: float) -> str:
    return f"{100 * x:.1f}"


def headline_table(results: pd.DataFrame) -> str:
    """Markdown table of PAF and attributable deaths by age and sex, with 95% UIs."""
    lines = [
        "| Sex | Age | NHANES n | IHD deaths 2018 | PAF % (95% UI) | Attributable deaths (95% UI) |",
        "|---|---|---|---|---|---|",
    ]
    for _, r in results.iterrows():
        lines.append(
            f"| {r['sex']} | {r['age_group']} | {r['n_nhanes']:,} | {r['ihd_deaths_2018']:,} | "
            f"{pct(r['paf_mean'])} ({pct(r['paf_lower'])} to {pct(r['paf_upper'])}) | "
            f"{r['attrib_deaths_mean']:,.0f} ({r['attrib_deaths_lower']:,.0f} to {r['attrib_deaths_upper']:,.0f}) |"
        )
    return "\n".join(lines) + "\n"


def sensitivity_table(sens: pd.DataFrame) -> str:
    """Markdown table of the overall 40+ PAF under each scenario."""
    lines = ["| Scenario | PAF % (95% UI) | Attributable deaths (95% UI) |", "|---|---|---|"]
    for _, r in sens.iterrows():
        lines.append(
            f"| {r['scenario']} | {pct(r['paf_mean'])} ({pct(r['paf_lower'])} to {pct(r['paf_upper'])}) | "
            f"{r['attrib_deaths_mean']:,.0f} ({r['attrib_deaths_lower']:,.0f} to {r['attrib_deaths_upper']:,.0f}) |"
        )
    return "\n".join(lines) + "\n"


def figure_paf(results: pd.DataFrame, exposure: pd.DataFrame, path: Path) -> None:
    """Left: mean SBP by age and sex. Right: PAF by age and sex with 95% UIs."""
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11, 4.4))
    x = np.arange(len(AGE_LABELS))
    for i, sex in enumerate(SEXES):
        off = (i - 0.5) * 0.18
        e = exposure[exposure["sex"] == sex].set_index("age_group").loc[list(AGE_LABELS)]
        ax0.errorbar(x + off, e["mean_sbp"], yerr=1.96 * e["se"], fmt="o-", color=COLORS[sex],
                     capsize=3, label=sex)
        r = results[(results["sex"] == sex) & results["age_group"].isin(AGE_LABELS)]
        r = r.set_index("age_group").loc[list(AGE_LABELS)]
        y = 100 * r["paf_mean"]
        err = [y - 100 * r["paf_lower"], 100 * r["paf_upper"] - y]
        ax1.errorbar(x + off, y, yerr=err, fmt="o", color=COLORS[sex], capsize=3, label=sex)
    ax0.axhspan(TMREL_LOW, TMREL_HIGH, color="#2f855a", alpha=0.15, label="TMREL 110 to 115")
    ax0.set(xticks=x, xticklabels=AGE_LABELS, xlabel="Age group", ylabel="Mean SBP (mmHg)",
            title="Exposure: mean SBP, NHANES 2017-2018 (95% CI)")
    ax1.set(xticks=x, xticklabels=AGE_LABELS, xlabel="Age group", ylabel="PAF (%)", ylim=(0, 80),
            title="PAF: IHD deaths due to SBP above TMREL (95% UI)")
    for ax in (ax0, ax1):
        ax.grid(axis="y", alpha=0.3)
        ax.legend(frameon=False, loc="lower right" if ax is ax1 else "upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def figure_sensitivity(sens: pd.DataFrame, benchmark: dict, path: Path) -> None:
    """Overall 40+ PAF under each scenario, against the published GBD 2019 US value."""
    fig, ax = plt.subplots(figsize=(9, 4.2))
    y = np.arange(len(sens))[::-1]
    mean = 100 * sens["paf_mean"].to_numpy()
    err = [mean - 100 * sens["paf_lower"].to_numpy(), 100 * sens["paf_upper"].to_numpy() - mean]
    ax.errorbar(mean, y, xerr=err, fmt="o", color="#2d3748", capsize=3)
    ax.axvspan(100 * benchmark["lower"], 100 * benchmark["upper"], color="#a0aec0", alpha=0.25,
               label="GBD 2019 benchmark:\nUSA, all ages, 2019 (95% UI)")
    ax.axvline(100 * benchmark["mean"], color="#718096", lw=1)
    ax.set(yticks=y, yticklabels=sens["scenario"], xlabel="PAF of IHD deaths, adults 40+ (%)",
           title="Sensitivity of the overall PAF", xlim=(0, 80))
    ax.grid(axis="x", alpha=0.3)
    ax.legend(frameon=False, loc="center right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
