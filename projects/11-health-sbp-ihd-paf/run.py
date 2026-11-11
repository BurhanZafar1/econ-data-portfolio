"""Run the whole analysis: exposure, PAF draws, attributable deaths, sensitivity, outputs.

    python run.py

Reads data/ only (no network). Every number in the README is written to output/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from sbp_paf import AGE_LABELS, SEXES  # noqa: E402
from sbp_paf.estimates import DrawInputs, attributable, cell_draws, share_attributable_below  # noqa: E402
from sbp_paf.extract import age_group  # noqa: E402
from sbp_paf.report import figure_paf, figure_sensitivity, headline_table, sensitivity_table  # noqa: E402
from sbp_paf.risks import draw_tmrel, ettehad_cells, load_psc  # noqa: E402
from sbp_paf.survey import rao_wu_weights, taylor_se_mean  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "output"
SEED = 20261111
N_DRAWS = 1000

# External benchmark, not used in estimation: GBD 2019 Risk Factors Collaborators,
# Lancet 2020, appendix 2, Table S3, high SBP to IHD, USA, both sexes, all ages, 2019, deaths.
GBD2019_USA_IHD_DEATHS_PAF = {"mean": 0.452, "lower": 0.338, "upper": 0.570}


def check(condition: bool, message: str) -> None:
    """Stop the run if a plausibility check fails."""
    if not condition:
        raise SystemExit(f"PLAUSIBILITY CHECK FAILED: {message}")
    print(f"  ok  {message}")


def exposure_table(extract: pd.DataFrame) -> pd.DataFrame:
    """Design based mean SBP, its Taylor SE and share above 115 mmHg for every cell."""
    rows = []
    for sex in SEXES:
        for age in AGE_LABELS:
            dom = ((extract["sex"] == sex) & (extract["age_group"] == age)).to_numpy()
            args = (extract["wt_mec"].to_numpy(), dom, extract["stratum"].to_numpy(), extract["psu"].to_numpy())
            mean, se = taylor_se_mean(extract["sbp"].to_numpy(), *args)
            above, _ = taylor_se_mean((extract["sbp"] > 115).to_numpy(float), *args)
            rows.append({"sex": sex, "age_group": age, "n": int(dom.sum()),
                         "mean_sbp": mean, "se": se, "share_above_115": above})
    return pd.DataFrame(rows)


def scenario_row(name: str, results: pd.DataFrame) -> dict:
    """The overall (both sexes, 40+) row of a results table, labelled by scenario."""
    row = results[(results["sex"] == "Both") & (results["age_group"] == "40+")].iloc[0].to_dict()
    return {"scenario": name, **{k: row[k] for k in row if k.startswith(("paf_", "attrib_"))}}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    extract = pd.read_csv(DATA / "nhanes_sbp_2017_2018.csv.gz")
    extract["age_group"] = age_group(extract["age"])
    deaths_all = pd.read_csv(DATA / "who_us_ihd_deaths_2018.csv")
    deaths = deaths_all[deaths_all["age_group"].isin(AGE_LABELS)]
    psc = load_psc(DATA / "psc2002_ihd_hazard_ratios.csv", sex_specific=True)

    # Shared random inputs: replicate weights, standard normal RR draws, TMREL draws.
    inputs = DrawInputs(
        rep_weights=rao_wu_weights(extract, N_DRAWS, rng),
        beta_z=rng.standard_normal((len(psc), N_DRAWS)),
        tmrel=draw_tmrel(N_DRAWS, rng),
    )

    print("Exposure")
    exposure = exposure_table(extract)
    exposure.to_csv(OUT / "exposure_sbp_age_sex.csv", index=False, float_format="%.4f")

    print("Main estimate")
    main_cells = cell_draws(extract, psc, inputs)
    results = attributable(main_cells, deaths)
    results.to_csv(OUT / "paf_ihd_age_sex.csv", index=False, float_format="%.6f")

    print("Sensitivity")
    scenarios = {
        "Main: PSC sex specific HRs, TMREL U(110, 115)": main_cells,
        "PSC HRs for both sexes combined": cell_draws(
            extract, load_psc(DATA / "psc2002_ihd_hazard_ratios.csv", sex_specific=False), inputs),
        "PSC HRs fully correlated across cells": cell_draws(extract, psc.assign(source="PSC shared"), inputs),
        "TMREL fixed at 115 mmHg": cell_draws(extract, psc, inputs, tmrel=np.full(N_DRAWS, 115.0)),
        "TMREL fixed at 110 mmHg": cell_draws(extract, psc, inputs, tmrel=np.full(N_DRAWS, 110.0)),
        "Usual SBP: deviations shrunk by 0.8 (illustrative)": cell_draws(extract, psc, inputs, shrink=0.8),
        "Trial RR for CHD events (Ettehad 2016)": cell_draws(extract, ettehad_cells(), inputs),
    }
    sens = pd.DataFrame([scenario_row(name, attributable(c, deaths)) for name, c in scenarios.items()])
    sens.to_csv(OUT / "sensitivity_overall.csv", index=False, float_format="%.6f")

    print("Plausibility checks")
    cells = results[results["age_group"].isin(AGE_LABELS)]
    overall = results[(results["sex"] == "Both") & (results["age_group"] == "40+")].iloc[0]
    check(len(extract) > 3000 and extract["sbp"].between(60, 270).all(), "SBP values within 60 to 270 mmHg")
    for sex in SEXES:
        means = exposure[exposure["sex"] == sex]["mean_sbp"].to_numpy()
        check(means[-1] > means[0], f"mean SBP is higher at 80+ than at 40-49 ({sex})")
    check(exposure["mean_sbp"].between(110, 150).all(), "cell mean SBP within 110 to 150 mmHg")
    check(cells["paf_lower"].gt(0).all() and cells["paf_upper"].lt(1).all(), "all cell PAFs within (0, 1)")
    check(((results["paf_lower"] <= results["paf_mean"]) & (results["paf_mean"] <= results["paf_upper"])).all(),
          "every 95% UI contains its mean")
    check(((results["paf_lower"] <= results["paf_central"]) & (results["paf_central"] <= results["paf_upper"])).all(),
          "every 95% UI contains the central (no draw) estimate")
    check(int(deaths["deaths"].sum()) == int(cells["ihd_deaths_2018"].sum()), "cell deaths reconcile with WHO file")
    all_ages = int(deaths_all[deaths_all["age_group"] == "all ages"]["deaths"].sum())
    check(deaths["deaths"].sum() <= all_ages, "deaths 40+ do not exceed all age deaths")
    check(abs(cells["attrib_deaths_mean"].sum() - overall["attrib_deaths_mean"]) < 1.0,
          "cell attributable deaths add up to the overall total")
    rep_totals = inputs.rep_weights.sum(axis=0)
    check(abs(rep_totals.mean() / extract["wt_mec"].sum() - 1) < 0.02,
          "bootstrap weights reproduce the population total on average")

    headline = {
        "n_draws": N_DRAWS,
        "seed": SEED,
        "n_nhanes_40plus": int(len(extract)),
        "ihd_deaths_40plus_2018": int(deaths["deaths"].sum()),
        "ihd_deaths_all_ages_2018": all_ages,
        "paf_40plus": {k: float(overall[f"paf_{k}"]) for k in ("mean", "lower", "upper", "central")},
        "attributable_deaths_40plus": {k: float(overall[f"attrib_deaths_{k}"]) for k in ("mean", "lower", "upper")},
        "share_of_attributable_deaths_from_sbp_below_140": share_attributable_below(extract, psc, deaths, 140.0),
        "gbd2019_usa_benchmark": GBD2019_USA_IHD_DEATHS_PAF,
    }
    (OUT / "headline.json").write_text(json.dumps(headline, indent=2) + "\n")
    (OUT / "headline_tables.md").write_text(
        "## PAF by age and sex\n\n" + headline_table(results)
        + "\n## Sensitivity, adults 40+\n\n" + sensitivity_table(sens))
    figure_paf(results, exposure, OUT / "fig1_paf_by_age_sex.png")
    figure_sensitivity(sens, GBD2019_USA_IHD_DEATHS_PAF, OUT / "fig2_sensitivity.png")
    print(json.dumps(headline, indent=2))


if __name__ == "__main__":
    main()
