"""Estimate the JEC cartel overcharge and damages; write every output.

Usage:  python run.py
Writes output/overcharge_table.csv and .md, output/validation_by_episode.csv,
output/headline.json, output/price_and_but_for.png, output/overcharge_by_method.png.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from overcharge.analysis import run  # noqa: E402
from overcharge.data import load_jec  # noqa: E402
from overcharge.figures import estimates_chart, price_chart  # noqa: E402

OUT = ROOT / "output"


def markdown_table(table: pd.DataFrame) -> str:
    """Readable version of the results table: percents and millions of dollars."""
    def millions(x: float) -> str:
        return "" if pd.isna(x) else f"{x / 1e6:.2f}"

    shown = pd.DataFrame(
        {
            "Method": table["method"],
            "Damage weeks": table["damage_weeks"],
            "b (log points)": table["log_overcharge_b"].map(lambda x: "" if pd.isna(x) else f"{x:.3f}"),
            "HAC s.e.": table["hac_se"].map(lambda x: "" if pd.isna(x) else f"{x:.3f}"),
            "Overcharge %": (100 * table["overcharge_pct_of_but_for"]).map(lambda x: f"{x:.1f}"),
            "Damages $m": table["damages_usd"].map(millions),
            "95% low $m": table["damages_low_usd"].map(millions),
            "95% high $m": table["damages_high_usd"].map(millions),
        }
    )
    return shown.to_markdown(index=False)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    df = load_jec()
    results = run(df)

    results.table.to_csv(OUT / "overcharge_table.csv", index=False, float_format="%.6f")
    (OUT / "overcharge_table.md").write_text(markdown_table(results.table) + "\n")
    results.validation.to_csv(OUT / "validation_by_episode.csv", index=False, float_format="%.6f")
    (OUT / "headline.json").write_text(json.dumps(results.headline, indent=2) + "\n")
    price_chart(df, results.forecast_price, results.preferred.b, OUT / "price_and_but_for.png")
    estimates_chart(results.table, OUT / "overcharge_by_method.png")

    h = results.headline
    print(markdown_table(results.table))
    print()
    print(f"Affected commerce: ${h['affected_commerce_usd'] / 1e6:.2f}m over {h['cartel_weeks']} cartel weeks")
    print(f"Preferred overcharge: {100 * h['preferred_overcharge_pct']:.1f}% above the but for price "
          f"({100 * h['preferred_overcharge_share_of_actual']:.1f}% of the price paid)")
    print(f"Preferred damages: ${h['preferred_damages_usd'] / 1e6:.2f}m "
          f"(95% interval ${h['preferred_damages_low_usd'] / 1e6:.2f}m to ${h['preferred_damages_high_usd'] / 1e6:.2f}m)")
    print(f"Placebo shifts as large as the real cartel effect: "
          f"{h['permutation_placebos_as_large']} of {h['permutation_placebos']} (p = {h['permutation_p_value']:.4f})")
    print(f"Forecast model, held out price wars: average absolute error per held out war (weighted by weeks) {100 * h['validation_mean_abs_pct_error_weighted']:.1f}%, "
          f"mean error {100 * h['validation_mean_pct_error_weighted']:+.1f}%")
    print(f"Demand elasticity (IV): {h['demand_elasticity']:.3f} (s.e. {h['demand_elasticity_se']:.3f}); "
          f"volume effect {100 * h['lost_pct']:.1f}% of cartel tonnage, deadweight loss ${h['deadweight_loss_usd'] / 1e6:.2f}m")
    print(f"Outputs written to {OUT.name}/")


if __name__ == "__main__":
    main()
