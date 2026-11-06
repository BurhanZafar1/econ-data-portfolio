"""Reproduce every table, chart and number in the README: python run.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from linkage import fellegi_sunter, report  # noqa: E402
from linkage.blocking import DEFAULT_PASSES, blocking_quality, candidate_pairs, pairs_for_pass  # noqa: E402
from linkage.compare import FIELD_RULES, compare_pairs  # noqa: E402
from linkage.data import load_file, true_links  # noqa: E402
from linkage.evaluate import exact_rule, one_to_one, score_links, threshold_curve  # noqa: E402

DATA = ROOT / "data"
OUTPUT = ROOT / "output"
LINK_THRESHOLD = 0.5
REVIEW_BAND = (0.05, 0.95)
EXACT_FIELDS = ["given_name", "surname", "date_of_birth"]
PERSON_ONLY_FIELDS = ["given_name", "surname", "date_of_birth", "state"]
PERSON_ONLY_PASSES = tuple(p for p in DEFAULT_PASSES if p.name != "postcode")
CURVE_THRESHOLDS = np.array([0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99])


def blocking_table(left: pd.DataFrame, right: pd.DataFrame, links: pd.MultiIndex) -> pd.DataFrame:
    """Pairs and pair completeness for each pass alone and for the cumulative union."""
    rows = []
    for k, blocking_pass in enumerate(DEFAULT_PASSES, start=1):
        alone = pairs_for_pass(left, right, blocking_pass)
        cumulative = blocking_quality(candidate_pairs(left, right, DEFAULT_PASSES[:k]),
                                      links, len(left), len(right))
        rows.append({
            "pass": blocking_pass.name,
            "pairs_alone": len(alone),
            "completeness_alone": len(alone.intersection(links)) / len(links),
            "pairs_cumulative": int(cumulative["candidate_pairs"]),
            "completeness_cumulative": cumulative["pair_completeness"],
        })
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    left = load_file(DATA / "febrl4_a.csv")
    right = load_file(DATA / "febrl4_b.csv")
    links = true_links(left, right)

    pairs = candidate_pairs(left, right)
    blocking = blocking_quality(pairs, links, len(left), len(right))
    levels = compare_pairs(left, right, pairs)
    n_levels = {rule.field: rule.n_levels for rule in FIELD_RULES}
    model = fellegi_sunter.fit(levels, n_levels)
    posterior = model.posterior(levels)
    weights = model.match_weight(levels)

    # Stress test: no address fields at all, so the postcode blocking pass is
    # dropped too and only the name and birth date passes generate candidates.
    person_pairs = candidate_pairs(left, right, PERSON_ONLY_PASSES)
    person_levels = compare_pairs(left, right, person_pairs)[PERSON_ONLY_FIELDS]
    person_model = fellegi_sunter.fit(person_levels,
                                      {f: n_levels[f] for f in PERSON_ONLY_FIELDS})
    person_posterior = person_model.posterior(person_levels)

    above = posterior[posterior >= LINK_THRESHOLD]
    person_above = person_posterior[person_posterior >= LINK_THRESHOLD]
    methods = {
        "Exact merge on name and birth date": exact_rule(left, right, EXACT_FIELDS),
        "Fellegi-Sunter, all fields": above.index,
        "Fellegi-Sunter, all fields, one to one": one_to_one(above),
        "Fellegi-Sunter, names, birth date, state": person_above.index,
        "Fellegi-Sunter, names, birth date, state, one to one": one_to_one(person_above),
    }
    comparison = pd.DataFrame([{"method": name, **score_links(predicted, links)}
                               for name, predicted in methods.items()])
    comparison["true_links_total"] = len(links)

    in_band = (posterior > REVIEW_BAND[0]) & (posterior < REVIEW_BAND[1])
    is_true = posterior.index.isin(links)
    accepted = posterior >= LINK_THRESHOLD
    cutoff_weight = float(np.log2((1 - model.match_share) / model.match_share))
    headline = {
        "records_a": len(left),
        "records_b": len(right),
        "true_links": len(links),
        "full_cross_product": len(left) * len(right),
        "candidate_pairs": len(pairs),
        "reduction_ratio": blocking["reduction_ratio"],
        "pair_completeness": blocking["pair_completeness"],
        "em_iterations": model.iterations,
        "estimated_match_share": model.match_share,
        "estimated_matches_in_candidates": model.match_share * len(pairs),
        "true_matches_in_candidates": int(is_true.sum()),
        "model_predicted_precision_at_0.5": float(posterior[accepted].mean()),
        "actual_precision_at_0.5": float(is_true[accepted].mean()),
        "person_only_candidate_pairs": len(person_pairs),
        "person_only_pair_completeness": len(person_pairs.intersection(links)) / len(links),
        "person_only_model_predicted_precision": float(person_above.mean()),
        "person_only_actual_precision": float(person_above.index.isin(links).mean()),
        "review_band_pairs": int(in_band.sum()),
        "review_band_true_share": float(is_true[in_band].mean()),
        "match_weight_cutoff_bits": cutoff_weight,
    }

    comparison.drop(columns="true_links_total").to_csv(OUTPUT / "method_comparison.csv", index=False)
    (OUTPUT / "method_comparison.md").write_text(
        report.markdown_table(comparison.drop(columns="true_links_total")))
    blocking_table(left, right, links).to_csv(OUTPUT / "blocking_passes.csv", index=False)
    fellegi_sunter.parameter_table(model).to_csv(OUTPUT / "m_u_parameters.csv", index=False)
    threshold_curve(posterior, links, CURVE_THRESHOLDS).to_csv(
        OUTPUT / "threshold_curve.csv", index=False)
    (OUTPUT / "headline.json").write_text(json.dumps(headline, indent=2) + "\n")

    report.weight_histogram(weights, is_true, cutoff_weight, OUTPUT / "match_weights.png")
    report.method_chart(comparison, OUTPUT / "method_comparison.png")

    print(report.markdown_table(comparison.drop(columns="true_links_total")))
    for key, value in headline.items():
        print(f"{key}: {value:,.4f}" if isinstance(value, float) else f"{key}: {value:,}")


if __name__ == "__main__":
    main()
