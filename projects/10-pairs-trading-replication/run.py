"""Reproduce every table, chart and number in the README: python run.py (about 7 minutes)."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pairs import analysis, data, paper, portfolio, stats  # noqa: E402

OUT = ROOT / "output"
SEED = 20061
PAPER = paper.SAMPLE
OOS = ("2003-01", "2026-09")  # industries end with the Sep 2026 CRSP update
OOS_YAHOO = ("2003-01", "2026-10")
COST_BP = 5.0  # per leg per side, assumed for liquid large caps and sector ETFs


def pct(x: float, d: int = 2) -> str:
    return f"{100 * x:.{d}f}%"


def replication_table(ind: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows, keep = [], {}
    for panel, wait in (("no_wait", 0), ("wait_one_day", 1)):
        for name, top in (("Top 5", 5), ("Top 20", 20), ("All", None)):
            res = portfolio.run(ind, *PAPER, portfolio.Config(top=top, wait=wait))
            m = res.monthly
            p_full, _, p_t, p_comm = paper.TABLE1[panel][name]
            per = res.periods
            rows.append(
                {
                    "panel": "No waiting" if wait == 0 else "Wait one day",
                    "portfolio": name,
                    "paper fully invested": pct(p_full, 3),
                    "ours fully invested": pct(m["fully"].mean(), 3),
                    "paper t (fully invested)": f"{p_t:.2f}",
                    "ours t (fully invested)": f"{m['fully'].mean() / stats.newey_west_se(m['fully'].to_numpy()):.2f}",
                    "paper committed": pct(p_comm, 3),
                    "ours committed": pct(m["committed"].mean(), 3),
                    "ours t (committed)": f"{m['committed'].mean() / stats.newey_west_se(m['committed'].to_numpy()):.2f}",
                    "paper round trips": f"{paper.TABLE2[name][1]:.2f}" if wait == 0 else "",
                    "ours round trips": f"{per['round_trips'].mean():.2f}",
                    "paper months open per pair": f"{paper.TABLE2[name][2]:.2f}" if wait == 0 else "",
                    "ours months open per pair": f"{per['months_open'].mean():.2f}",
                    "ours pairs traded": f"{per['n_pairs'].mean():.1f}",
                }
            )
            keep[(panel, name)] = res
    return pd.DataFrame(rows), keep


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    ind = data.industry_returns()
    etf = data.etf_returns()
    stk = data.stock_returns()
    mem = data.membership()
    factors = data.factors_monthly()
    eligible = lambda d: data.member_on(mem, stk.columns, d)  # noqa: E731
    head: dict = {"seed": SEED, "cost_bp_per_leg_side": COST_BP}

    # Survivorship coverage of the stock universe: current members with data / all members then
    end = mem["end_date"].fillna(pd.Timestamp.max)
    head["stock_coverage"] = {
        d: {"members": int(((mem["start_date"] <= d) & (end > d)).sum()),
            "in_sample": int(eligible(pd.Timestamp(d)).sum())}
        for d in ("2002-01-02", "2014-01-02", "2025-05-01")
    }

    # 1. Replication of Table 1 on survivorship free industry portfolios, 1963-2002
    table1, kept = replication_table(ind)
    (OUT / "table1_replication.md").write_text(table1.to_markdown(index=False) + "\n")
    table1.to_csv(OUT / "table1_replication.csv", index=False)
    head["industry_paper_period"] = {
        f"{p}|{n}": {"committed": float(r.monthly["committed"].mean()), "fully": float(r.monthly["fully"].mean())}
        for (p, n), r in kept.items()
    }
    head["paper_implied_cost_bp"] = 1e4 * paper.implied_round_trip_cost(0.0144, 0.0090, 2.0)

    # 2. Stress tests and out of sample, headline rule: wait one day, committed capital
    universes = {
        "Industries 1963-1988": (ind, ("1963-07", "1988-12"), portfolio.Config(top=20, wait=1)),
        "Industries 1989-2002": (ind, ("1989-01", "2002-12"), portfolio.Config(top=20, wait=1)),
        "Industries 2003-2026": (ind, OOS, portfolio.Config(top=20, wait=1)),
        "Sector ETFs 2003-2026": (etf, OOS_YAHOO, portfolio.Config(top=5, wait=1)),
        "S&P 500 stocks 2003-2026": (stk, OOS_YAHOO, portfolio.Config(top=20, wait=1, eligible=eligible)),
    }
    rows, series = [], {}
    for label, (ret, (a, b), cfg) in universes.items():
        res = portfolio.run(ret, a, b, cfg)
        x = res.monthly["committed"]
        series[label] = x
        s = analysis.summarize(x, rng)
        net = portfolio.run(ret, a, b, replace(cfg, cost=COST_BP / 1e4)).monthly["committed"]
        be = analysis.break_even_cost(ret, a, b, cfg)
        s.update(
            {
                "pairs": int(cfg.top),
                "active_strategies_min": int(res.monthly["n_active"].min()),
                "months_with_six_active": int((res.monthly["n_active"] == 6).sum()),
                "round_trips": float(res.periods["round_trips"].mean()),
                "universe": float(res.periods["n_universe"].mean()),
                "net_mean": float(net.mean()),
                "net_sharpe_annual": float(stats.sharpe(net.to_numpy()) * np.sqrt(12)),
                "break_even_bp": 1e4 * be,
            }
        )
        head[label] = s
        rows.append(
            {
                "sample": label,
                "months": s["months"],
                "avg universe": f"{s['universe']:.0f}",
                "pairs": s["pairs"],
                "mean (gross)": pct(s["mean"], 3),
                "NW t": f"{s['nw_t']:.2f}",
                "95% CI (bootstrap)": f"{pct(s['ci_low'], 3)} to {pct(s['ci_high'], 3)}",
                "Sharpe (annual)": f"{s['sharpe_annual']:.2f}",
                "round trips": f"{s['round_trips']:.2f}",
                "break even cost (bp per leg per side)": (
                    "n/a (gross < 0)" if np.isnan(s["break_even_bp"]) else f"{s['break_even_bp']:.1f}"),
                f"mean net of {COST_BP:.0f} bp": pct(s["net_mean"], 3),
                "Sharpe net": f"{s['net_sharpe_annual']:.2f}",
            }
        )
    table2 = pd.DataFrame(rows)
    (OUT / "table2_stress_out_of_sample.md").write_text(table2.to_markdown(index=False) + "\n")
    table2.to_csv(OUT / "table2_stress_out_of_sample.csv", index=False)

    # 3. Placebo: same rule on random pairs
    plac = {}
    for label, draws in (("Industries 1963-2002", 50), ("S&P 500 stocks 2003-2026", 100)):
        if label.startswith("Industries"):
            ret, (a, b), cfg = ind, PAPER, portfolio.Config(top=20, wait=1)
            actual = kept[("wait_one_day", "Top 20")].monthly["committed"].mean()
        else:
            ret, (a, b), cfg = universes[label]
            actual = series[label].mean()
        means = analysis.placebo_means(ret, a, b, cfg, draws, SEED)
        plac[label] = means
        head[f"placebo|{label}"] = {
            "draws": draws,
            "actual": float(actual),
            "placebo_mean": float(means.mean()),
            "placebo_p95": float(np.quantile(means, 0.95)),
            "share_placebo_above_actual": float((means >= actual).mean()),
        }

    # 4. Multiple testing: deflated Sharpe ratio over the 24 variants tried on stocks
    a, b = OOS_YAHOO
    trial_sr, grid, trial_series = [], [], []
    for k in (1.5, 2.0, 2.5, 3.0):
        for top in (5, 20, None):
            for wait in (0, 1):
                m = portfolio.run(stk, a, b, portfolio.Config(top=top, k=k, wait=wait, eligible=eligible)).monthly
                trial_sr.append(stats.sharpe(m["committed"].to_numpy()))
                trial_series.append(m["committed"].to_numpy())
                grid.append({"k": k, "top": "all" if top is None else top, "wait": wait,
                             "mean": float(m["committed"].mean()), "sharpe_monthly": trial_sr[-1]})
    pd.DataFrame(grid).to_csv(OUT / "stock_trial_grid.csv", index=False)
    x = series["S&P 500 stocks 2003-2026"].to_numpy()
    dsr, sr0 = stats.deflated_sharpe(x, np.array(trial_sr))
    best_i = int(np.argmax(trial_sr))
    dsr_best, _ = stats.deflated_sharpe(trial_series[best_i], np.array(trial_sr))
    corr = np.corrcoef(np.vstack(trial_series))
    head["dsr_stocks"] = {"trials": len(trial_sr), "dsr_headline": dsr, "dsr_best_trial": dsr_best,
                          "sr0_monthly": sr0, "headline_sr_monthly": stats.sharpe(x), "best_trial": grid[best_i],
                          "mean_pairwise_corr_of_trials": float(corr[np.triu_indices(len(corr), 1)].mean())}

    # 5. Factor exposures
    fac_rows = []
    for label, x in (("Industries 1963-2002", kept[("wait_one_day", "Top 20")].monthly["committed"]),
                     ("S&P 500 stocks 2003-2026", series["S&P 500 stocks 2003-2026"])):
        reg = analysis.factor_regression(x, factors)
        head[f"factors|{label}"] = {i: {"coef": float(r.coef), "t": float(r.t)} for i, r in reg.iterrows()}
        head[f"factors|{label}"]["r2"] = float(reg["r2"].iloc[0])
        for i, r in reg.iterrows():
            fac_rows.append({"sample": label, "term": i, "coef": f"{r.coef:.4f}", "t": f"{r.t:.2f}"})
    pd.DataFrame(fac_rows).to_markdown(OUT / "table3_factor_regressions.md", index=False)

    # Figures
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ind_full = portfolio.run(ind, "1963-07", OOS[1], portfolio.Config(top=20, wait=1)).monthly["committed"]
    head["industries_full_1963_2026_mean"] = float(ind_full.mean())
    for lab, s, c in (("49 industries, top 20", ind_full, "#3b6ea8"),
                      ("S&P 500 members today, top 20", series["S&P 500 stocks 2003-2026"], "#c0504d"),
                      ("9 sector ETFs, top 5", series["Sector ETFs 2003-2026"], "#5b9b5b")):
        ax.plot(s.index.to_timestamp(), (1 + s).cumprod(), label=lab, color=c, lw=1.4)
    ax.axvspan(pd.Timestamp("1963-07-01"), pd.Timestamp("2002-12-31"), color="0.92", label="paper sample")
    ax.set_yscale("log")
    ax.set_ylabel("Growth of $1, committed capital (log)")
    ax.set_title("Distance rule, wait one day, before costs")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_cumulative.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, (label, means) in zip(axes, plac.items()):
        actual = head[f"placebo|{label}"]["actual"]
        ax.hist(100 * means, bins=20, color="0.7")
        ax.axvline(100 * actual, color="#c0504d", lw=2, label="distance pairs")
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("Mean monthly return, % (committed)")
        ax.legend(frameon=False, fontsize=8)
    axes[0].set_ylabel("Random pair draws")
    fig.suptitle("Placebo: same rule on randomly drawn pairs", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_placebo.png", dpi=150)
    plt.close(fig)

    (OUT / "headline.json").write_text(json.dumps(head, indent=2, default=str) + "\n")
    print(table1.to_markdown(index=False))
    print(table2.to_markdown(index=False))
    print(json.dumps({k: v for k, v in head.items() if k.startswith(("placebo", "dsr"))}, indent=1, default=str))


if __name__ == "__main__":
    main()
