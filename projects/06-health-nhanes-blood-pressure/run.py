"""Reproduce every table, chart and number in the README: python run.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from nhanes_bp import report  # noqa: E402
from nhanes_bp.estimates import MEASURES, add_indicators, age_specific, change_between, estimate_all  # noqa: E402
from nhanes_bp.standards import (  # noqa: E402
    NCHS_GROUPS,
    US_2000_ADULT,
    WHO_2000_2025,
    WHO_ADULT_GROUPS,
    aggregate_weights,
)

DATA = ROOT / "data"
OUTPUT = ROOT / "output"
FIRST, LAST = "1999-2000", "2017-2018"
AGE_PROFILE_GROUPS = [(20, 29), (30, 39), (40, 49), (50, 59), (60, 69), (70, 79), (80, 200)]


def validate_against_nchs(frame: pd.DataFrame) -> pd.DataFrame:
    """Rebuild NCHS Data Brief 364 Figure 4 (18+, 130/80 definition, US 2000 standard)."""
    weights = aggregate_weights(US_2000_ADULT, NCHS_GROUPS)
    htn130 = tuple(m for m in MEASURES if m.name == "htn130")
    ours = estimate_all(frame, NCHS_GROUPS, weights, measures=htn130)
    ours = ours[ours["type"] == "age_standardized"]
    published = pd.read_csv(DATA / "benchmarks" / "nchs_db364_figure4.csv")
    compare = published.merge(ours, on=["cycle", "sex"]).rename(
        columns={"percent": "published", "se_x": "published_se", "estimate": "ours", "se_y": "ours_se"}
    )
    compare["difference"] = compare["ours"] - compare["published"]
    compare["z"] = compare["difference"] / compare["published_se"]
    return compare[["cycle", "sex", "published", "published_se", "ours", "ours_se", "difference", "z", "n"]]


def plausibility_checks(table: pd.DataFrame, ages: pd.DataFrame) -> list[str]:
    """Checks a reviewer would run by eye; any failure stops the run."""
    failures = []
    if not ((table["lower95"] <= table["estimate"]) & (table["estimate"] <= table["upper95"])).all():
        failures.append("an interval does not contain its estimate")
    pct = table[table["measure"] != "sbp"]["estimate"]
    if not pct.between(0, 100).all():
        failures.append("a prevalence is outside 0-100")
    sbp = table[table["measure"] == "sbp"]["estimate"]
    if not sbp.between(105, 140).all():
        failures.append("a population mean SBP is outside 105-140 mmHg")
    wide = table.pivot_table(index=["cycle", "sex", "type"], columns="measure", values="estimate")
    if not (wide["htn130"] >= wide["htn140"]).all():
        failures.append("the 130/80 prevalence is below the 140/90 prevalence")
    for sex, rows in ages[ages["measure"] == "sbp"].groupby("sex"):
        if rows["estimate"].iloc[-1] - rows["estimate"].iloc[0] < 10:
            failures.append(f"mean SBP does not rise with age for {sex}")
    return failures


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    frame = add_indicators(pd.read_csv(DATA / "nhanes_bp_extract.csv.gz"))

    who_weights = aggregate_weights(WHO_2000_2025, WHO_ADULT_GROUPS)
    table = estimate_all(frame, WHO_ADULT_GROUPS, who_weights)
    table.round(4).to_csv(OUTPUT / "estimates_who_standard.csv", index=False)

    compare = validate_against_nchs(frame)
    compare.round(3).to_csv(OUTPUT / "validation_nchs_db364.csv", index=False)

    ages = pd.concat(
        [age_specific(frame, LAST, AGE_PROFILE_GROUPS, m).assign(measure=m.name) for m in MEASURES],
        ignore_index=True,
    )
    ages.round(3).to_csv(OUTPUT / f"age_specific_{LAST}.csv", index=False)

    change = change_between(table, FIRST, LAST)
    change.round(3).to_csv(OUTPUT / "change_1999_2018.csv", index=False)

    # Sensitivity: does the conclusion depend on the choice of standard population?
    us_weights = aggregate_weights(US_2000_ADULT, WHO_ADULT_GROUPS)
    htn140 = tuple(m for m in MEASURES if m.name == "htn140")
    us_table = estimate_all(frame[frame["cycle"].isin([FIRST, LAST])], WHO_ADULT_GROUPS, us_weights, htn140)
    us_change = change_between(us_table, FIRST, LAST)
    us_table.round(4).to_csv(OUTPUT / "sensitivity_us2000_standard.csv", index=False)

    failures = plausibility_checks(table, ages)
    if failures:
        raise SystemExit("Plausibility checks failed: " + "; ".join(failures))

    headline = report.headline_table(table, FIRST, LAST)
    (OUTPUT / "headline_table.md").write_text(report.to_markdown(headline))
    report.plot_trends(table, OUTPUT / "fig1_trends.png")
    report.plot_validation(compare, OUTPUT / "fig2_validation_nchs.png")

    def pick(measure: str, sex: str, kind: str, cycle: str) -> dict[str, float]:
        row = table.query("measure == @measure and sex == @sex and type == @kind and cycle == @cycle").iloc[0]
        return {k: round(float(row[k]), 1) for k in ("estimate", "lower95", "upper95")}

    def pick_change(measure: str, sex: str, kind: str) -> dict[str, float]:
        row = change.query("measure == @measure and sex == @sex and type == @kind").iloc[0]
        return {k: round(float(row[k]), 1) for k in ("change", "lower95", "upper95")}

    both = compare[compare["sex"] == "Both"]
    summary = {
        "analysis_sample_n_by_cycle": table.query("measure == 'sbp' and sex == 'Both' and type == 'crude'")
        .set_index("cycle")["n"].astype(int).to_dict(),
        "htn140_age_std": {c: pick("htn140", "Both", "age_standardized", c) for c in (FIRST, LAST)},
        "htn140_crude": {c: pick("htn140", "Both", "crude", c) for c in (FIRST, LAST)},
        "sbp_age_std": {s: {c: pick("sbp", s, "age_standardized", c) for c in (FIRST, LAST)}
                        for s in ("Male", "Female")},
        "change_htn140_age_std": pick_change("htn140", "Both", "age_standardized"),
        "change_htn140_crude": pick_change("htn140", "Both", "crude"),
        "change_sbp_age_std": {s: pick_change("sbp", s, "age_standardized") for s in ("Both", "Male", "Female")},
        "sensitivity_us2000_htn140_age_std": {c: {k: round(float(r[k]), 1) for k in ("estimate", "lower95", "upper95")}
                                              for c, r in us_table.query("sex == 'Both' and type == 'age_standardized'")
                                              .set_index("cycle").iterrows()},
        "sensitivity_us2000_change_htn140": {k: round(float(v), 1) for k, v in us_change.query(
            "sex == 'Both' and type == 'age_standardized'").iloc[0][["change", "lower95", "upper95"]].items()},
        "validation_max_abs_diff_pp": round(float(compare["difference"].abs().max()), 2),
        "validation_max_abs_diff_pp_all_adults": round(float(both["difference"].abs().max()), 2),
        "validation_max_abs_z": round(float(compare["z"].abs().max()), 2),
        "validation_n_2017_2018": int(both.query("cycle == @LAST")["n"].iloc[0]),
        "who_weights_20plus": who_weights.round(6).to_dict(),
    }
    (OUTPUT / "headline.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "who_weights_20plus"}, indent=2))


if __name__ == "__main__":
    main()
