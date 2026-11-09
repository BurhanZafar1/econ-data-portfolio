"""Run the whole analysis: paired estimates, validation, crosswalk, BRFSS adjustment, outputs.

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

from htn_crosswalk.application import adjust_brfss, crosswalk_table, national_check  # noqa: E402
from htn_crosswalk.extract import AGE_LABELS, add_age_group  # noqa: E402
from htn_crosswalk.paired import paired_estimates  # noqa: E402
from htn_crosswalk.report import figure_gap, figure_validation_and_states, markdown_table  # noqa: E402
from htn_crosswalk.validation import candidate_specs, rolling_origin, score, split_selection_test  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "output"
SEED = 20261109
HEADLINE_YEAR, HEADLINE_CYCLE = 2017, "2017-2018"


def select(scores: pd.DataFrame) -> str:
    """The crosswalk candidate with the lowest out of sample mean absolute error."""
    crosswalks = scores[scores["key"].str.startswith("crosswalk")]
    return str(crosswalks.loc[crosswalks["mae_pp"].idxmin(), "key"])


def check(condition: bool, message: str) -> None:
    """Stop the run if a plausibility check fails."""
    if not condition:
        raise SystemExit(f"PLAUSIBILITY CHECK FAILED: {message}")
    print(f"  ok  {message}")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    extract = add_age_group(pd.read_csv(DATA / "nhanes_htn_extract.csv.gz"))
    brfss = pd.read_csv(DATA / "brfss_hbp_age_2011_2017.csv")

    # 1. Paired estimates for every cycle and cell.
    paired_sex = paired_estimates(extract, ["xw_group", "sex"])
    paired_xw = paired_estimates(extract, ["xw_group"])
    paired_age = paired_estimates(extract, ["age_group"])  # BRFSS age groups, for checks only
    paired_sex.to_csv(OUT / "paired_estimates_age_sex.csv", index=False, float_format="%.9f")

    # 2. Rolling origin validation and model choice (age x sex is primary; age only is used for BRFSS).
    preds_sex, preds_age = rolling_origin(paired_sex, ["xw_group", "sex"]), rolling_origin(paired_xw, ["xw_group"])
    (select_sex, test_sex), (select_age, test_age) = split_selection_test(preds_sex), split_selection_test(preds_age)
    # The choice uses selection origins only; every reported error comes from the later test origins.
    chosen_sex, chosen_age = select(score(select_sex)), select(score(select_age))
    scores_sex, scores_age = score(test_sex), score(test_age)
    score(select_sex).to_csv(OUT / "validation_selection_scores_age_sex.csv", index=False, float_format="%.4f")
    scores_sex.to_csv(OUT / "validation_test_scores_age_sex.csv", index=False, float_format="%.4f")
    scores_age.to_csv(OUT / "validation_test_scores_age.csv", index=False, float_format="%.4f")
    preds_sex.to_csv(OUT / "validation_predictions_age_sex.csv", index=False, float_format="%.6f")
    spec_sex, spec_age = candidate_specs(True)[chosen_sex], candidate_specs(False)[chosen_age]

    # 3. Final crosswalk and 4. BRFSS adjustment with 1,000 draws.
    table = crosswalk_table(paired_sex, spec_sex)
    table.to_csv(OUT / "crosswalk_age_sex.csv", index=False, float_format="%.9f")
    adjusted = adjust_brfss(brfss, paired_xw, spec_age, rng)
    adjusted.to_csv(OUT / "brfss_adjusted_state_age.csv", index=False, float_format="%.2f")
    national = national_check(adjusted, paired_age, HEADLINE_YEAR, HEADLINE_CYCLE)
    national.to_csv(OUT / "national_check_2017.csv", index=False, float_format="%.2f")

    # 5. Plausibility checks.
    print("Plausibility checks")
    meas = paired_age.pivot(index="cycle", columns="age_group", values="p_meas")[list(AGE_LABELS)]
    check(bool((meas.diff(axis=1).iloc[:, 1:] > 0).all().all()), "measured prevalence rises with age in every cycle")
    for col in ("p_self", "p_meas", "sens", "spec"):
        check(bool(paired_sex[col].between(0, 1, inclusive="neither").all()), f"{col} strictly between 0 and 1, every cell")
    check(bool(((table["d_lower"] < table["d"]) & (table["d"] < table["d_upper"])).all()),
          "crosswalk intervals contain the estimate")
    inside = (adjusted["adjusted_lower_pct"] <= adjusted["adjusted_pct"]) & (
        adjusted["adjusted_pct"] <= adjusted["adjusted_upper_pct"])
    check(bool(inside.all()), "every adjusted 95% UI contains its mean")
    check(bool((preds_sex["n_train_cycles"] >= 3).all()), "each validation origin fitted on at least 3 earlier cycles")
    gap = (national["adjusted_pct"] - national["nhanes_measured_pct"]).abs()
    print(f"  max 2017 gap, median state vs NHANES measured: {gap.max():.2f} points")
    check(bool((gap < 5).all()), "2017 state median after adjustment within 5 points of NHANES measured, every age")

    # 6. Headline numbers, tables and figures.
    dropped = len(brfss) - len(adjusted)
    best_sex = scores_sex.set_index("key")
    headline = {
        "analysed_adults": int((extract["analysis"] == 1).sum()),
        "chosen_crosswalk_age_sex": chosen_sex,
        "chosen_crosswalk_age": chosen_age,
        "crosswalk_cycles": table["cycles"].iloc[0],
        "tau": float(table["tau"].iloc[0]),
        "selection_origins": sorted(select_sex["cycle"].unique()),
        "test_origins": sorted(test_sex["cycle"].unique()),
        "validation_test_cells": int(best_sex.loc["p_self", "cells"]),
        "mae_no_adjustment_pp": float(best_sex.loc["p_self", "mae_pp"]),
        "mae_sens_spec_pp": float(best_sex.loc["rogan_gladen", "mae_pp"]),
        "mae_sens_spec_latest_3_pp": float(best_sex.loc["rogan_gladen_latest_3", "mae_pp"]),
        "mae_chosen_pp": float(best_sex.loc[chosen_sex, "mae_pp"]),
        "bias_chosen_pp": float(best_sex.loc[chosen_sex, "bias_pp"]),
        "coverage_chosen": float(best_sex.loc[chosen_sex, "coverage_95"]),
        "age_only_model_mae_pp": float(scores_age.set_index("key").loc[chosen_age, "mae_pp"]),
        "age_only_model_coverage": float(scores_age.set_index("key").loc[chosen_age, "coverage_95"]),
        "brfss_2017_cells": int((adjusted["year"] == HEADLINE_YEAR).sum()),
        "brfss_2017_cells_ui_excludes_self_report": int(
            ((adjusted["year"] == HEADLINE_YEAR) & ~adjusted["self_report_pct"].between(
                adjusted["adjusted_lower_pct"], adjusted["adjusted_upper_pct"])).sum()),
        "brfss_rows_adjusted": int(len(adjusted)),
        "brfss_rows_suppressed_by_cdc": int(dropped),
    }
    (OUT / "headline.json").write_text(json.dumps(headline, indent=2) + "\n")

    show = table.assign(
        **{
            "Self report %": (100 * table["p_self"]).round(1),
            "Measured %": (100 * table["p_meas"]).round(1),
            "Sensitivity %": (100 * table["sens"]).round(0).astype(int),
            "Specificity %": (100 * table["spec"]).round(0).astype(int),
            "Crosswalk d (95% CI)": [f"{d:+.2f} ({lo:+.2f} to {hi:+.2f})"
                                     for d, lo, hi in zip(table["d"], table["d_lower"], table["d_upper"])],
        }
    )[["xw_group", "sex", "Self report %", "Measured %", "Sensitivity %", "Specificity %", "Crosswalk d (95% CI)"]]
    nat = national.round(1)
    states_2017 = adjusted[adjusted["year"] == HEADLINE_YEAR]
    example = states_2017[states_2017["age_group"] == "65+"].sort_values("adjusted_pct")
    lines = [
        "## Crosswalk by age and sex", markdown_table(show.rename(columns={"xw_group": "Age", "sex": "Sex"})),
        "", "## Validation test origins 2013-2014 to 2017-2018 (age x sex cells; choice made on earlier origins)",
        markdown_table(scores_sex[["method", "cells", "bias_pp", "mae_pp", "max_abs_error_pp", "coverage_95"]].round(2)),
        "", "## 2017 check: median of states vs NHANES 2017-2018", markdown_table(nat),
        "", "## BRFSS 2017, age 65+, lowest and highest adjusted states",
        markdown_table(pd.concat([example.head(2), example.tail(2)])[
            ["state", "self_report_pct", "adjusted_pct", "adjusted_lower_pct", "adjusted_upper_pct"]].round(1)),
    ]
    (OUT / "headline_tables.md").write_text("\n".join(lines) + "\n")
    figure_gap(table, OUT / "fig1_self_vs_measured.png")
    figure_validation_and_states(scores_sex, adjusted, HEADLINE_YEAR, OUT / "fig2_validation_and_states.png")
    print(json.dumps(headline, indent=2))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
