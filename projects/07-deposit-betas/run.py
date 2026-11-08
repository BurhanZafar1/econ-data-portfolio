"""Reproduce every table, chart and number in the README: python run.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from deposit_beta import report  # noqa: E402
from deposit_beta.cycles import cycle_table  # noqa: E402
from deposit_beta.data import ERA_2021, PRODUCTS, add_changes, build_monthly_panel  # noqa: E402
from deposit_beta.regression import PassThrough, estimate_pass_through, pass_through_table  # noqa: E402
from deposit_beta.scenario import ILLUSTRATIVE_MIX, run_scenarios  # noqa: E402

RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "output"
MAIN_LAGS = 6
LAG_SENSITIVITY = (3, 6, 9)


def estimate_all(changes: pd.DataFrame) -> list[PassThrough]:
    """Main sample (FDIC 2021 method) and the pooled 2009-2026 robustness sample."""
    samples = {
        "fdic_2021_method": changes["era"].eq(ERA_2021),
        "pooled_2009_2026": changes["era"].notna(),
    }
    return [
        estimate_pass_through(changes, product, mask, name, lags)
        for name, mask in samples.items()
        for lags in LAG_SENSITIVITY
        for product in PRODUCTS
    ]


def sanity_checks(cycles: pd.DataFrame, main: pd.DataFrame, scenarios: pd.DataFrame) -> list[str]:
    """Economic plausibility checks; any failure stops the run."""
    failures = []
    if not cycles[["beta", "beta_at_last_move"]].stack().between(0, 1).all():
        failures.append("a cycle beta is outside [0, 1]")
    if not main[["beta_up", "beta_down"]].stack().between(-0.05, 1).all():
        failures.append("a long run beta is outside [-0.05, 1]")
    if main.set_index("product")["beta_up"].idxmax() != "cd_12m":
        failures.append("12-month CDs are not the most rate sensitive product")
    hike22 = cycles[cycles["cycle"] == "2022-2023 hikes"].set_index("product")["beta"]
    gap = (main.set_index("product")["beta_up"] - hike22).abs()
    if (gap > 0.10).any():
        failures.append("regression up betas disagree with the 2022 cycle betas by more than 0.10")
    end = scenarios[scenarios["month"] == scenarios["month"].max()].set_index("scenario")["cost_per_bn_musd"]
    if not end["Cut 100bp"] < end["Hold"] < end["Hike 50bp"]:
        failures.append("scenario deposit costs are not ordered cut < hold < hike")
    return failures


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    panel = build_monthly_panel(RAW)
    changes = add_changes(panel)
    panel.round(4).to_csv(OUTPUT / "monthly_panel.csv")

    cycles = cycle_table(panel, PRODUCTS)
    cycles.round(4).to_csv(OUTPUT / "cycle_betas.csv", index=False)

    results = estimate_all(changes)
    table = pass_through_table(results)
    table.round(4).to_csv(OUTPUT / "pass_through_all.csv", index=False)
    is_main = (table["sample"] == "fdic_2021_method") & (table["max_lag"] == MAIN_LAGS)
    main_table = table[is_main]
    main_fits = {r.product: r for r in results if r.sample == "fdic_2021_method" and r.max_lag == MAIN_LAGS}

    scenarios = run_scenarios(changes, main_fits)
    scenarios.round(4).to_csv(OUTPUT / "scenarios.csv", index=False)

    failures = sanity_checks(cycles, main_table, scenarios)
    if failures:
        raise SystemExit("Sanity checks failed:\n- " + "\n- ".join(failures))

    (OUTPUT / "headline_table.md").write_text(report.headline_table(cycles, main_table), encoding="utf-8")
    report.plot_rates(panel, OUTPUT / "fig1_rates.png")
    report.plot_beta_paths(panel, OUTPUT / "fig2_beta_paths.png")

    last = panel.iloc[-1]
    start_cost = sum(ILLUSTRATIVE_MIX[p] * last[p] for p in ILLUSTRATIVE_MIX) * 10
    end = scenarios[scenarios["month"] == 12].set_index("scenario")
    headline = {
        "sample": f"{panel.index[0]} to {panel.index[-1]}",
        "months": len(panel),
        "main_nobs": int(main_table["nobs"].iloc[0]),
        "last_month": str(panel.index[-1]),
        "fedfunds_last": float(last["fedfunds"]),
        "cost_per_bn_now_musd": round(float(start_cost), 3),
        "cost_per_bn_month12_musd": end["cost_per_bn_musd"].round(3).to_dict(),
        "cut_vs_hold_musd": round(float(end.loc["Cut 100bp", "cost_per_bn_musd"] - end.loc["Hold", "cost_per_bn_musd"]), 3),
        "hike_vs_hold_musd": round(float(end.loc["Hike 50bp", "cost_per_bn_musd"] - end.loc["Hold", "cost_per_bn_musd"]), 3),
    }
    (OUTPUT / "headline.json").write_text(json.dumps(headline, indent=2), encoding="utf-8")

    print(report.headline_table(cycles, main_table))
    print(main_table[["product", "nobs", "r_squared", "beta_up", "se_up", "beta_down", "se_down", "asym_p", "intercept", "intercept_se"]].round(3).to_string(index=False))
    print(json.dumps(headline, indent=2))
    print("All sanity checks passed.")


if __name__ == "__main__":
    main()
