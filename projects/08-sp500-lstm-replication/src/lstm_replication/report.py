"""Tables, charts and the headline numbers written to output/."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from . import features, paper  # noqa: E402


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _ci(row: pd.Series) -> str:
    return f"{row.auc:.2f} [{row.auc_lo:.2f}, {row.auc_hi:.2f}]"


def _span(frame: pd.DataFrame) -> str:
    return f"{frame.index[0]:%b %Y} to {frame.index[-1]:%b %Y}"


def _get(results: pd.DataFrame, variant: str, model: int) -> pd.Series:
    return results[(results.variant == variant) & (results.model == model)].iloc[0]


def replication_table(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for m, name in features.MODEL_NAMES.items():
        p = paper.TABLE1[m]
        lstm, base = _get(results, "lstm_replication", m), _get(results, "baseline_original", m)
        rows.append({
            "Model": m, "Features": name,
            "LSTM dev / test, paper": f"{_pct(p[0])} / {_pct(p[1])}",
            "LSTM dev / test, ours (seed 1)": f"{_pct(lstm.dev_accuracy)} / {_pct(lstm.seed1_accuracy)}",
            "LSTM test, 5 seeds": f"{_pct(lstm.accuracy_min)} to {_pct(lstm.accuracy_max)}",
            "Baseline dev / test, paper": f"{_pct(p[2])} / {_pct(p[3])}",
            "Baseline dev / test, ours": f"{_pct(base.dev_accuracy)} / {_pct(base.accuracy)}",
            "AUC LSTM / baseline, paper": f"{p[4]:.2f} / {p[5]:.2f}",
            "AUC LSTM (5 seeds) / baseline, ours": f"{lstm.auc_min:.2f} to {lstm.auc_max:.2f} / {base.auc:.2f}",
        })
    return pd.DataFrame(rows)


def stress_table(results: pd.DataFrame, prefix: str, base_variant: str, lstm_variant: str) -> pd.DataFrame:
    rows = []
    for m, name in features.MODEL_NAMES.items():
        base, lstm = _get(results, base_variant, m), _get(results, lstm_variant, m)
        rows.append({
            "Model": m, "Features": name, "Always up accuracy": _pct(base.always_up),
            "Baseline accuracy": _pct(base.accuracy), "Baseline AUC [95% CI]": _ci(base),
            f"LSTM {prefix} accuracy": _pct(lstm.accuracy), f"LSTM {prefix} AUC [95% CI]": _ci(lstm),
            "LSTM predicts up": _pct(lstm.share_pred_up),
        })
    return pd.DataFrame(rows)


def auc_chart(results: pd.DataFrame, variants: dict[str, str], title: str, path: Path, show_paper: bool) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    models = list(features.MODEL_NAMES)
    offsets = [-0.15, 0.15]
    colors = ["#1f5fa8", "#c4572b"]
    for (variant, label), off, color in zip(variants.items(), offsets, colors):
        sub = results[results.variant == variant].set_index("model").loc[models]
        x = [m + off for m in models]
        ax.errorbar(x, sub.auc, yerr=[sub.auc - sub.auc_lo, sub.auc_hi - sub.auc], fmt="o", color=color,
                    capsize=3, label=f"{label} (95% block bootstrap CI)")
    if show_paper:
        ax.scatter([m - 0.15 for m in models], [paper.TABLE1[m][5] for m in models], marker="x", color="#1f5fa8",
                   label="Baseline, paper")
        ax.scatter([m + 0.15 for m in models], [paper.TABLE1[m][4] for m in models], marker="x", color="#c4572b",
                   label="LSTM, paper")
    ax.axhline(0.5, color="black", linestyle="--", linewidth=1)
    ax.text(7.45, 0.505, "no skill", ha="right", fontsize=8)
    ax.set_xticks(models)
    ax.set_xticklabels([features.MODEL_NAMES[m].replace(" + ", "\n+ ") for m in models], fontsize=8)
    ax.set_ylabel("Test AUC")
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_all(results: pd.DataFrame, paper_sample, ext, out: Path) -> dict:
    rep = replication_table(results)
    test = stress_table(results, "(scaled, 5 seed average)", "baseline_original", "lstm_scaled")
    oos = stress_table(results, "(scaled, 3 seed average)", "baseline_extension", "lstm_extension_scaled")
    m3 = _get(results, "baseline_paper_params", 3)
    note = (f"\nModel 3 baseline: our random search ranks a different candidate first. Refitting the setting the "
            f"notebook printed (l1, alpha 1.84e-05) gives test accuracy {_pct(m3.accuracy)} and AUC {m3.auc:.2f}, "
            f"the paper's numbers, with {int(m3.n_selected)} selected features.\n")
    for name, table in (("table1_replication", rep), ("table2_paper_test_period", test), ("table3_out_of_sample_2019_2026", oos)):
        table.to_csv(out / f"{name}.csv", index=False)
        extra = note if name == "table1_replication" else ""
        (out / f"{name}.md").write_text(table.to_markdown(index=False) + "\n" + extra)
    auc_chart(results, {"baseline_original": "Logistic baseline", "lstm_scaled": "LSTM, scaled inputs"},
              f"Test AUC, paper's test period ({_span(paper_sample.test)})", out / "fig1_auc_paper_period.png", True)
    auc_chart(results, {"baseline_extension": "Logistic baseline", "lstm_extension_scaled": "LSTM, scaled inputs"},
              f"Test AUC, new out of sample period ({_span(ext.test)})", out / "fig2_auc_out_of_sample.png", False)

    def n_significant(variant: str) -> int:
        return int((results[results.variant == variant].auc_lo > 0.5).sum())

    rep_lstm = results[results.variant == "lstm_replication"]
    model3_paper_params_test_accuracy = round(float(m3.accuracy), 4)
    return {
        "paper_test_period": f"{paper_sample.test.index[0].date()} to {paper_sample.test.index[-1].date()}",
        "out_of_sample_period": f"{ext.test.index[0].date()} to {ext.test.index[-1].date()}",
        "n_test_paper": len(paper_sample.test), "n_test_out_of_sample": len(ext.test),
        "always_up_paper_test": round(float(paper_sample.test["label"].mean()), 4),
        "always_up_out_of_sample": round(float(ext.test["label"].mean()), 4),
        "replication_lstm_share_pred_up_min": round(float(rep_lstm.share_pred_up.min()), 4),
        "model3_paper_params_test_accuracy": model3_paper_params_test_accuracy,
        "models_auc_ci_above_half": {v: n_significant(v) for v in
            ["baseline_original", "baseline_purged", "lstm_replication", "lstm_scaled",
             "baseline_extension", "lstm_extension_replication", "lstm_extension_scaled"]},
        "best_out_of_sample_auc": round(float(results[results.variant.isin(
            ["baseline_extension", "lstm_extension_scaled"])].auc.max()), 4),
    }
