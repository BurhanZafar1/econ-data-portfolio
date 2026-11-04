"""Reproduce every table, chart and number: python run.py."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from staggered_did import aggregate, bacon, report, simulate, twfe  # noqa: E402
from staggered_did.group_time import estimate_group_time  # noqa: E402
from staggered_did.inference import (  # noqa: E402
    standard_errors,
    sup_t_critical_value,
    wald_pretest,
)
from staggered_did.panel import Panel, drop_cohort, load_minimum_wage  # noqa: E402
from staggered_did.placebo import (  # noqa: E402
    leave_one_state_out,
    randomization_test,
    state_placebo_test,
)

DATA = ROOT / "data" / "mpdta.csv"
OUTPUT = ROOT / "output"
BAND_SEED = 20260001
SIMULATION_SEED = 20260002
RANDOMIZATION_SEED = 20260003
RANDOMIZATION_DRAWS = 2000
SIMULATION_DRAWS = 3000
SIMULATION_UNITS = 500
LONG_DIFFERENCE = "Same weights, all pre years as base"
ILLINOIS_FIPS = 17
ILLINOIS_COHORT = 2004


def _row(name: str, estimate: float, influence: np.ndarray, panel: Panel) -> dict[str, object]:
    """One line of the results table from one influence function."""
    column = influence[:, None]
    return {
        "estimator": name,
        "estimate": estimate,
        "se_county": float(standard_errors(column)[0]),
        "se_state": float(standard_errors(column, panel.clusters)[0]),
    }


def _overall(result: aggregate.Aggregate) -> tuple[float, np.ndarray]:
    return float(result.estimate[-1]), result.influence[:, -1]


def build_estimates(panel: Panel, with_population: Panel) -> pd.DataFrame:
    """Assemble the headline comparison of estimators."""
    main = estimate_group_time(panel)
    not_yet = estimate_group_time(panel, control="notyet")
    adjusted = estimate_group_time(with_population)
    no_illinois_panel = drop_cohort(panel, ILLINOIS_COHORT)
    no_illinois = estimate_group_time(no_illinois_panel)

    static = twfe.static_twfe(panel)
    rows: list[dict[str, object]] = [{
        "estimator": "TWFE, single post dummy",
        "estimate": float(static.coef[0]),
        "se_county": float(static.se_unit[0]),
        "se_state": float(static.se_cluster[0]),
    }]
    specs = [
        ("CS overall, cohort weighted (preferred)", aggregate.group_att(main), panel),
        ("CS simple, all treated cells", aggregate.simple_att(main), panel),
        ("CS event study average", aggregate.event_study(main), panel),
        ("CS event study average, same cohorts at years 0 and 1",
         aggregate.event_study(main, balance_e=1), panel),
        ("CS overall, not yet treated as controls", aggregate.group_att(not_yet), panel),
        ("CS overall, adjusting for log population",
         aggregate.group_att(adjusted), with_population),
        ("CS overall, without Illinois",
         aggregate.group_att(no_illinois), no_illinois_panel),
    ]
    for name, result, sample in specs:
        estimate, influence = _overall(result) if len(result.labels) > 1 else (
            float(result.estimate[0]), result.influence[:, 0]
        )
        rows.append(_row(name, estimate, influence, sample))
    rows.append({
        "estimator": LONG_DIFFERENCE,
        "estimate": bacon.cohort_weighted_long_difference(bacon.decompose(panel), panel),
    })
    table = pd.DataFrame(rows)
    table["ci_low_state"] = table["estimate"] - 1.96 * table["se_state"]
    table["ci_high_state"] = table["estimate"] + 1.96 * table["se_state"]
    return table


def build_event_study(panel: Panel) -> pd.DataFrame:
    """Event study table with joint bands and TWFE leads and lags alongside.

    Uses the universal base year so that both estimators measure every point
    against event time -1, the omitted year.
    """
    main = estimate_group_time(panel, base_period="universal")
    dynamic = aggregate.event_study(main)
    points = dynamic.influence[:, :-1]
    estimates = dynamic.estimate[:-1]
    se_state = standard_errors(points, panel.clusters)
    critical = sup_t_critical_value(points, panel.clusters, seed=BAND_SEED)
    states = aggregate.treated_states_by_event_time(main)
    table = pd.DataFrame({
        "event_time": dynamic.labels[:-1],
        "estimate": estimates,
        "se_county": standard_errors(points),
        "se_state": se_state,
        "band_low": estimates - critical * se_state,
        "band_high": estimates + critical * se_state,
        "treated_states": [states[int(e)] for e in dynamic.labels[:-1]],
    })
    # A cluster band has no meaning when a single state is treated.
    table["band_reliable"] = table["treated_states"] > 1
    leads_lags = twfe.event_study_twfe(panel).rename(columns={
        "estimate": "twfe_estimate", "se_state": "twfe_se_state",
    })
    return table.merge(leads_lags, on="event_time", how="left")


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    (ROOT / "report").mkdir(exist_ok=True)
    panel = load_minimum_wage(DATA)
    with_population = load_minimum_wage(DATA, ("lpop",))

    estimates = build_estimates(panel, with_population)
    estimates.to_csv(OUTPUT / "estimates.csv", index=False)
    (OUTPUT / "estimates.md").write_text(
        report.estimates_markdown(estimates), encoding="utf-8"
    )

    decomposition = bacon.decompose(panel)
    decomposition.to_csv(OUTPUT / "bacon_decomposition.csv", index=False)
    bacon_summary = bacon.summarize(decomposition)
    bacon_summary.to_csv(OUTPUT / "bacon_summary.csv", index=False)
    twfe_estimate = float(estimates["estimate"].iloc[0])
    rebuilt = float((decomposition["weight"] * decomposition["estimate"]).sum())
    if not np.isclose(rebuilt, twfe_estimate, atol=1e-10):
        raise RuntimeError("Bacon components do not rebuild the TWFE coefficient")

    group_time = estimate_group_time(panel)
    cells = group_time.table.copy()
    cells["se_county"] = standard_errors(group_time.influence)
    cells["se_state"] = standard_errors(group_time.influence, panel.clusters)
    cells.to_csv(OUTPUT / "group_time_effects.csv", index=False)

    pre = ~cells["post"].to_numpy()
    pre_estimates = cells["att"].to_numpy()[pre]
    pre_county = wald_pretest(pre_estimates, group_time.influence[:, pre])
    pre_state = wald_pretest(pre_estimates, group_time.influence[:, pre], panel.clusters)
    pd.DataFrame(
        [("county", *pre_county), ("state", *pre_state)],
        columns=["clustering", "wald", "df", "p_value"],
    ).to_csv(OUTPUT / "pretest.csv", index=False)

    one_year = aggregate.event_study(group_time)
    one_year_leads = pd.DataFrame({
        "event_time": one_year.labels[:-1],
        "att": one_year.estimate[:-1],
    })

    placebo = state_placebo_test(panel, ILLINOIS_COHORT, ILLINOIS_FIPS)
    placebo.to_csv(OUTPUT / "illinois_placebo.csv", index=False)

    event = build_event_study(panel)
    event.to_csv(OUTPUT / "event_study.csv", index=False)
    report.plot_event_study(
        event, placebo[placebo["year"] != "average"].astype({"year": int}),
        ILLINOIS_COHORT, OUTPUT / "event_study.png",
    )
    report.plot_bacon(decomposition, twfe_estimate, OUTPUT / "bacon_weights.png")

    randomization = randomization_test(panel, RANDOMIZATION_DRAWS, RANDOMIZATION_SEED)
    randomization.to_csv(OUTPUT / "randomization_test.csv", index=False)
    leave_one_out = leave_one_state_out(panel)
    leave_one_out.to_csv(OUTPUT / "leave_one_state_out.csv", index=False)

    simulation = pd.concat([
        simulate.monte_carlo(design, SIMULATION_DRAWS, SIMULATION_UNITS, SIMULATION_SEED)
        for design in (simulate.STRESS_TEST, simulate.SAMPLE_SHAPED)
    ], ignore_index=True)
    simulation.to_csv(OUTPUT / "simulation_check.csv", index=False)

    lookup = estimates.set_index("estimator")["estimate"]
    average_placebo = placebo.set_index("year").loc["average"]
    state_se = estimates.set_index("estimator")["se_state"]
    bacon_weights = bacon_summary.set_index("type")["weight"]
    report.write_summary(ROOT / "report" / "summary.md", {
        "twfe": twfe_estimate,
        "twfe_t": twfe_estimate / float(state_se["TWFE, single post dummy"]),
        "long_difference": float(lookup[LONG_DIFFERENCE]),
        "randomization_p": float(randomization["p_value_estimate"].iloc[0]),
        "already_treated_weight": float(bacon_weights[bacon.LATE_VS_EARLY]),
        "group_overall": float(lookup["CS overall, cohort weighted (preferred)"]),
        "dynamic_overall": float(lookup["CS event study average"]),
        "balanced_overall": float(
            lookup["CS event study average, same cohorts at years 0 and 1"]
        ),
        "illinois_as_extreme": float(average_placebo["n_as_extreme"]),
        "illinois_placebos": float(average_placebo["n_placebos"]),
        "illinois_p": float(average_placebo["p_value"]),
        "lead_one": float(one_year_leads.set_index("event_time").loc[-1, "att"]),
    })

    pd.set_option("display.width", 140, "display.max_columns", 20)
    print(estimates.round(4).to_string(index=False))
    print("\nGoodman-Bacon summary\n", bacon_summary.round(4).to_string(index=False))
    print("\nEvent study\n", event.round(4).to_string(index=False))
    print("\nPre test county, state:", pre_county, pre_state)
    print("\nIllinois placebo\n", placebo.round(4).to_string(index=False))
    print("\nRandomization test\n", randomization.round(4).to_string(index=False))
    print("\nLeave one state out\n", leave_one_out["estimate"].describe().round(4).to_string())
    print("\nSimulated check (not real data)\n", simulation.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
