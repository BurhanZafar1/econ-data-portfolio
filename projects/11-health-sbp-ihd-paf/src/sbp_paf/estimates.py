"""Draws based PAF estimates by age and sex, attributable deaths and aggregates.

Every draw d combines three independent sources of uncertainty:
  * exposure: one Rao-Wu bootstrap replicate of the NHANES design weights,
  * relative risk: one normal draw of the log slope for each age and sex cell,
  * TMREL: one uniform draw on [110, 115] mmHg.
Deaths are registered counts and are held fixed. Summaries are the mean and the
2.5th and 97.5th percentiles of the draws (a 95% uncertainty interval).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from sbp_paf import AGE_LABELS, SEXES
from sbp_paf.paf import relative_risk, weighted_paf
from sbp_paf.risks import TMREL_HIGH, TMREL_LOW

CENTRAL_TMREL = 0.5 * (TMREL_LOW + TMREL_HIGH)


@dataclass(frozen=True)
class DrawInputs:
    """Random inputs shared by all scenarios (common random numbers make scenarios comparable)."""

    rep_weights: np.ndarray  # (n_people, n_draws)
    beta_z: np.ndarray  # (n_sources, n_draws) standard normal, one row per published estimate
    tmrel: np.ndarray  # (n_draws,)


def cell_index(sex: str, age: str) -> int:
    """Row position of a cell in the canonical (sex, age group) order."""
    return SEXES.index(sex) * len(AGE_LABELS) + AGE_LABELS.index(age)


def shrink_toward_mean(sbp: np.ndarray, weights: np.ndarray, factor: float) -> np.ndarray:
    """Pull each value toward the weighted cell mean: m + factor (x - m).

    factor 1 leaves the single occasion distribution unchanged; factor < 1 is a
    simple stand in for the narrower distribution of usual (long run) SBP.
    """
    mean = np.average(sbp, weights=weights)
    return mean + factor * (sbp - mean)


def cell_draws(extract: pd.DataFrame, cells: pd.DataFrame, inputs: DrawInputs,
               tmrel: np.ndarray | None = None, shrink: float = 1.0) -> pd.DataFrame:
    """PAF draws and the central estimate for every (sex, age group) cell.

    cells must be in canonical order (see cell_index). tmrel overrides the
    uniform TMREL draws, for fixed TMREL sensitivity runs.
    Returns one row per cell with 'central' and a 'draws' array column.
    """
    tmrel_draws = inputs.tmrel if tmrel is None else tmrel
    central_tmrel = CENTRAL_TMREL if tmrel is None else float(np.mean(tmrel))
    # Cells that share one published estimate share one random draw of it.
    sources = list(dict.fromkeys(cells["source"]))
    out = []
    for sex in SEXES:
        for age in AGE_LABELS:
            k = cell_index(sex, age)
            cell = cells.iloc[k]
            assert (cell["sex"], cell["age_group"]) == (sex, age), "cells are not in canonical order"
            rows = ((extract["sex"] == sex) & (extract["age_group"] == age)).to_numpy()
            weights = extract["wt_mec"].to_numpy()[rows]
            sbp = shrink_toward_mean(extract["sbp"].to_numpy()[rows], weights, shrink)
            betas = cell["beta"] + cell["beta_se"] * inputs.beta_z[sources.index(cell["source"])]
            draws = weighted_paf(sbp, inputs.rep_weights[rows], betas, tmrel_draws)
            central = weighted_paf(sbp, weights, cell["beta"], central_tmrel)
            out.append({"sex": sex, "age_group": age, "n": int(rows.sum()),
                        "central": central, "draws": draws})
    return pd.DataFrame(out)


def summarise(draws: np.ndarray) -> dict[str, float]:
    """Mean and 95% uncertainty interval of a vector of draws."""
    lower, upper = np.percentile(draws, [2.5, 97.5])
    return {"mean": float(draws.mean()), "lower": float(lower), "upper": float(upper)}


def attributable(cells_out: pd.DataFrame, deaths: pd.DataFrame) -> pd.DataFrame:
    """Cell, sex and overall (40+) attributable deaths and PAFs, with 95% UIs.

    Aggregate PAF = sum(PAF_cell x deaths_cell) / sum(deaths_cell), computed draw by draw.
    """
    merged = cells_out.merge(deaths, on=["sex", "age_group"], how="left", validate="one_to_one")
    if merged["deaths"].isna().any():
        raise ValueError("Missing deaths for some cells")
    rows = []
    for _, r in merged.iterrows():
        rows.append(_row(r["sex"], r["age_group"], r["n"], r["deaths"], r["central"], r["draws"]))
    groups = [(sex, merged[merged["sex"] == sex]) for sex in SEXES] + [("Both", merged)]
    for label, grp in groups:
        deaths_total = grp["deaths"].sum()
        att_draws = sum(row["draws"] * row["deaths"] for _, row in grp.iterrows())
        att_central = float((grp["central"] * grp["deaths"]).sum())
        rows.append(_row(label, "40+", int(grp["n"].sum()), deaths_total,
                         att_central / deaths_total, att_draws / deaths_total))
    return pd.DataFrame(rows)


def _row(sex: str, age: str, n: int, deaths: float, central: float, draws: np.ndarray) -> dict:
    """One output row: PAF central, mean, UI and the attributable deaths implied."""
    paf = summarise(draws)
    att = summarise(draws * deaths)
    return {
        "sex": sex, "age_group": age, "n_nhanes": n, "ihd_deaths_2018": int(deaths),
        "paf_central": central, "paf_mean": paf["mean"], "paf_lower": paf["lower"], "paf_upper": paf["upper"],
        "attrib_deaths_mean": att["mean"], "attrib_deaths_lower": att["lower"], "attrib_deaths_upper": att["upper"],
    }


def share_attributable_below(extract: pd.DataFrame, cells: pd.DataFrame, deaths: pd.DataFrame,
                             threshold: float) -> float:
    """Share of central attributable deaths arising from people with SBP below threshold.

    Within a cell, attributable deaths are D * sum_i w_i (RR_i - 1) / sum_i w_i RR_i,
    so each person contributes in proportion to w_i (RR_i - 1).
    """
    total = below = 0.0
    for _, cell in cells.iterrows():
        rows = ((extract["sex"] == cell["sex"]) & (extract["age_group"] == cell["age_group"])).to_numpy()
        sbp, w = extract["sbp"].to_numpy()[rows], extract["wt_mec"].to_numpy()[rows]
        rr = relative_risk(sbp, cell["beta"], CENTRAL_TMREL)
        d = deaths.set_index(["sex", "age_group"]).loc[(cell["sex"], cell["age_group"]), "deaths"]
        contrib = d * w * (rr - 1.0) / (w * rr).sum()
        total += contrib.sum()
        below += contrib[sbp < threshold].sum()
    return below / total
