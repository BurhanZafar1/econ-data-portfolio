"""Reproduce every table, chart and number in the README: python run.py (about 10 seconds)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from tsmom import analysis, data, paper, stats, strategy  # noqa: E402

OUT = ROOT / "output"
SEED = 2012
PAPER = paper.SAMPLE
OOS_AQR = ("2010-01", "2026-05")  # last month in the AQR update used here
OOS = ("2010-01", "2026-10")
GRID = [1, 3, 6, 9, 12, 24, 36, 48]
FF = ["MKT", "SMB", "HML", "UMD"]
COSTS_BP = [1.0, 2.0, 5.0]


def pct(x: float, d: int = 2) -> str:
    return f"{100 * x:.{d}f}%"


def window(x, first, last):
    return x.loc[pd.Period(first, "M"): pd.Period(last, "M")]


def check_aqr_vintage() -> dict:
    now = data.aqr_checksums()
    recorded = data.aqr_recorded_checksums()
    if recorded and recorded != now:
        print("WARNING: the AQR files differ from the vintage behind the README numbers "
              "(AQR rebuilds its history at each update); AQR based numbers may move slightly.")
    if not recorded:
        (OUT / "aqr_checksums_used.json").write_text(json.dumps(now, indent=2) + "\n")
    return now


def check_raw_files() -> None:
    path = data.RAW / "SHA256SUMS.json"
    recorded = json.loads(path.read_text())
    now = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.RAW.glob("*")) if p.name != path.name}
    if recorded != now:
        print("WARNING: data/raw differs from the committed vintage (sources revise history); numbers may differ from the README.")


def fit_dict(fit: stats.OLS) -> dict:
    return {n: {"coef": float(c), "t": float(t)} for n, c, t in zip(fit.names, fit.coef, fit.t)} | {"r2": fit.r2, "nobs": fit.nobs}


def monthly_vol_expanding(monthly: pd.DataFrame) -> pd.DataFrame:
    daily, _ = data.daily_excess_returns()
    vols = {n: strategy.expanding_vol(r).groupby(r.index.to_period("M")).last() for n, r in daily.items()}
    return pd.DataFrame(vols).reindex(monthly.index)[monthly.columns]


def build_panel():
    daily, classes = data.daily_excess_returns()
    monthly, vol = strategy.monthly_panel(daily)
    return monthly, vol, classes


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    check_raw_files()
    head: dict = {"aqr_sha256": check_aqr_vintage()}
    ff = data.factors()
    orig = data.aqr_original()
    upd = data.aqr_updated()

    # ------------------------------------------------ A. the authors' own factor, paper window
    a = orig["TSMOM"]
    head["aqr_original"] = analysis.summarize(a, rng)
    t3m = analysis.factor_regression(a, ff, FF)
    t3q = analysis.factor_regression(a, ff, FF, quarterly=True)
    strad = analysis.straddle_regression(a, ff["MKT"])
    head["aqr_original_table3_monthly"] = fit_dict(t3m)
    head["aqr_original_table3_quarterly"] = fit_dict(t3q)
    head["aqr_original_straddle"] = fit_dict(strad)
    # alpha implied by the paper's own printed loadings on this file: mean minus sum beta * mean factor
    fw = ff.loc[a.index]
    head["implied_alpha_paper_betas"] = float(a.mean() - sum(paper.TABLE3_MONTHLY["coef"][f] * fw[f].mean() for f in FF))

    # ------------------------------------------------ B. rebuild from public prices
    monthly, vol, classes = build_panel()
    pos = strategy.positions(monthly, vol, k=12)
    inst = strategy.strategy_returns(monthly, pos)
    ours = strategy.portfolio(inst)
    ours_cls = {c: strategy.portfolio(inst, classes, c) for c in data.ASSET_CLASS}
    head["n_instruments"] = len(monthly.columns)
    head["n_by_class"] = {c: sum(v == c for v in classes.values()) for c in data.ASSET_CLASS}
    pw = window(ours, *PAPER)
    head["ours_paper"] = analysis.summarize(pw, rng)
    head["ours_paper_ci_by_block"] = {b: [float(x) for x in np.percentile(stats.block_bootstrap_sharpe(pw.to_numpy(), b, 2000, np.random.default_rng(SEED + b)), [2.5, 97.5])]
                                      for b in (6, 12, 24)}
    head["ours_paper_table3_monthly"] = fit_dict(analysis.factor_regression(pw, ff, FF))
    head["ours_paper_straddle"] = fit_dict(analysis.straddle_regression(pw, ff["MKT"]))
    corr = {"TSMOM": float(pd.concat([pw, orig["TSMOM"]], axis=1).dropna().corr().iloc[0, 1])}
    for c in data.ASSET_CLASS:
        corr[c] = float(pd.concat([window(ours_cls[c], *PAPER), orig[f"TSMOM^{c}"]], axis=1).dropna().corr().iloc[0, 1])
    head["corr_with_aqr_original"] = corr
    avail = monthly.notna() & pos.shift(1).notna()
    head["avg_instruments_paper_window"] = float(window(avail.sum(axis=1), *PAPER).mean())

    # per instrument TSMOM (paper Fig. 2): sign and significance, 1985 to 2009
    per = []
    for name in inst.columns:
        x = window(inst[name], *PAPER).dropna()
        if len(x) < 36:
            continue
        per.append({"instrument": name, "class": classes[name], "months": len(x), "sharpe": stats.sharpe(x.to_numpy()),
                    "t": x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))})
    per = pd.DataFrame(per).sort_values(["class", "sharpe"])
    per.to_csv(OUT / "per_instrument_sharpe_1985_2009.csv", index=False, float_format="%.3f")
    head["per_instrument"] = {"n": len(per), "positive": int((per["sharpe"] > 0).sum()),
                              "significant_5pct": int((per["t"] > 1.96).sum())}

    # predictive regressions (paper Fig. 1), 1985 to 2009 dependent months
    lagsfit = {("sign" if s else "return"): analysis.pooled_lag_tstats(monthly, vol, range(1, 61), s, *PAPER) for s in (False, True)}
    lag_table = pd.concat({k: v["t"] for k, v in lagsfit.items()}, axis=1)
    lag_table.to_csv(OUT / "lag_tstats_paper_fig1.csv", float_format="%.3f")
    head["lag_t"] = {k: {"positive_1_12": int((v["t"].loc[1:12] > 0).sum()), "significant_1_12": int((v["t"].loc[1:12] > 1.96).sum()),
                         "t_lag12": float(v["t"].loc[12]), "negative_13_60": int((v["t"].loc[13:60] < 0).sum())}
                     for k, v in lagsfit.items()}

    # ------------------------------------------------ C. stress tests (paper window, our rebuild)
    passive = strategy.strategy_returns(monthly, strategy.positions(monthly, vol, k=12, signal="long"))
    fac = ff.copy()
    fac["BOND"] = strategy.portfolio(passive, classes, "FI")
    fac["CMDTY"] = strategy.portfolio(passive, classes, "CM")
    grid_t, grid_sr, trial_sr = pd.DataFrame(index=GRID, columns=GRID, dtype=float), pd.DataFrame(index=GRID, columns=GRID, dtype=float), []
    months = []
    for k in GRID:
        for h in GRID:
            r = window(strategy.portfolio(strategy.strategy_returns(monthly, strategy.positions(monthly, vol, k=k, h=h))), *PAPER)
            fit = analysis.factor_regression(r, fac, FF + ["BOND", "CMDTY"], lags=12)
            grid_t.loc[k, h] = fit.t[0]
            grid_sr.loc[k, h] = stats.sharpe(r.to_numpy())
            trial_sr.append(r.mean() / r.std(ddof=1))
            months.append(len(r))
    grid_t.to_csv(OUT / "table3_grid_alpha_t.csv", float_format="%.2f")
    head["grid"] = {"t_12_1": float(grid_t.loc[12, 1]), "positive_short_block": int((grid_t.loc[[1, 3, 6, 9, 12], [1, 3, 6, 9, 12]] > 0).sum().sum()),
                    "best": [int(grid_sr.stack().idxmax()[0]), int(grid_sr.stack().idxmax()[1])], "best_sharpe": float(grid_sr.max().max()),
                    "months_min": min(months), "months_max": max(months)}
    dsr, sr0 = stats.deflated_sharpe(pw.to_numpy(), np.array(trial_sr))
    head["dsr_12_1"] = {"dsr": dsr, "sr0_annual": sr0 * np.sqrt(12), "trials": len(trial_sr)}
    head["hlz_t_threshold"] = 3.0

    # volatility scaling decomposition (Kim, Tse and Wald, 2016)
    unscaled_tsmom = window(strategy.portfolio(strategy.strategy_returns(monthly, strategy.positions(monthly, vol, 12, scaled=False))), *PAPER)
    scaled_long = window(strategy.portfolio(passive), *PAPER)
    unscaled_long = window(strategy.portfolio(strategy.strategy_returns(monthly, strategy.positions(monthly, vol, 12, scaled=False, signal="long"))), *PAPER)
    # volatility level without timing: expanding window volatility keeps cross asset risk parity
    xvol = monthly_vol_expanding(monthly)
    flat_tsmom = window(strategy.portfolio(strategy.strategy_returns(monthly, strategy.positions(monthly, xvol, 12))), *PAPER)
    flat_long = window(strategy.portfolio(strategy.strategy_returns(monthly, strategy.positions(monthly, xvol, 12, signal="long"))), *PAPER)
    vs = pd.DataFrame({"TSMOM, volatility scaled (paper)": pw, "TSMOM, expanding window volatility": flat_tsmom,
                       "TSMOM, equal notional": unscaled_tsmom, "Long only, volatility scaled": scaled_long,
                       "Long only, expanding window volatility": flat_long, "Long only, equal notional": unscaled_long})
    head["vol_scaling_sharpe"] = {c: stats.sharpe(vs[c].dropna().to_numpy()) for c in vs}
    fit_vs = stats.ols(pw.to_numpy(), scaled_long.reindex(pw.index).to_numpy(), ["long"], cov="nw", lags=12)
    head["tsmom_on_scaled_long"] = fit_dict(fit_vs)

    # transaction costs: turnover and break even
    to = strategy.turnover(pos).shift(1).reindex(pw.index).fillna(0.0)  # trades that create each month's return
    head["turnover_per_month"] = float(to.mean())
    head["break_even_bp"] = float(1e4 * pw.mean() / to.mean())
    head["net"] = {f"{c:g}bp": analysis.summarize(window(strategy.net_of_costs(ours, pos, c / 1e4), *PAPER), rng) for c in COSTS_BP}
    to_class = {c: float(window(strategy.turnover(pos[[n for n in pos if classes[n] == c]]), *PAPER).mean()) for c in data.ASSET_CLASS}
    head["turnover_by_class"] = to_class

    # ------------------------------------------------ D. out of sample after the paper
    head["aqr_updated_oos"] = analysis.summarize(window(upd["TSMOM"], *OOS_AQR), rng)
    head["aqr_updated_oos_ff"] = fit_dict(analysis.factor_regression(window(upd["TSMOM"], *OOS_AQR), ff, FF))
    head["aqr_updated_paper_window"] = analysis.summarize(window(upd["TSMOM"], *PAPER), rng)
    head["aqr_updated_paper_window_ff"] = fit_dict(analysis.factor_regression(window(upd["TSMOM"], *PAPER), ff, FF))
    head["corr_updated_vs_original"] = float(pd.concat([orig["TSMOM"], upd["TSMOM"]], axis=1).dropna().corr().iloc[0, 1])
    oos = window(ours, *OOS)
    head["ours_oos"] = analysis.summarize(oos, rng)
    head["ours_oos_net_2bp"] = analysis.summarize(window(strategy.net_of_costs(ours, pos, 2e-4), *OOS), rng)
    head["ours_oos_ff"] = fit_dict(analysis.factor_regression(oos, ff, FF))
    head["corr_ours_vs_updated_oos"] = float(pd.concat([oos, window(upd["TSMOM"], *OOS_AQR)], axis=1).dropna().corr().iloc[0, 1])
    head["ours_oos_by_class"] = {c: stats.sharpe(window(ours_cls[c], *OOS).dropna().to_numpy()) for c in data.ASSET_CLASS}
    head["aqr_oos_by_class"] = {c: stats.sharpe(window(upd[f"TSMOM^{c}"], *OOS_AQR).to_numpy()) for c in data.ASSET_CLASS}

    _tables(head, grid_t)
    _charts(orig, upd, ours, lag_table)
    (OUT / "headline.json").write_text(json.dumps(head, indent=2, default=float) + "\n")
    print(json.dumps({k: head[k] for k in ("aqr_original", "ours_paper", "corr_with_aqr_original", "dsr_12_1", "aqr_updated_oos", "ours_oos")},
                     indent=1, default=float))


def _tables(h: dict, grid_t: pd.DataFrame) -> None:
    p3, o3, r3 = paper.TABLE3_MONTHLY, h["aqr_original_table3_monthly"], h["ours_paper_table3_monthly"]
    rows = [
        ("Annualized volatility", pct(paper.FACTOR_VOL, 0), pct(h["aqr_original"]["vol_ann"], 1), pct(h["ours_paper"]["vol_ann"], 1)),
        ("Sharpe ratio", "> 1", f"{h['aqr_original']['sharpe']:.2f}", f"{h['ours_paper']['sharpe']:.2f}"),
        ("Mean excess return a month", "n/r", pct(h["aqr_original"]["mean_ann"] / 12), pct(h["ours_paper"]["mean_ann"] / 12)),
        ("Alpha a month (Table 3 A)", f"{pct(p3['coef']['const'])} (t {p3['t']['const']:.2f})",
         f"{pct(o3['const']['coef'])} (t {o3['const']['t']:.2f})", f"{pct(r3['const']['coef'])} (t {r3['const']['t']:.2f})"),
    ]
    for f in FF:
        rows.append((f"Beta on {'market' if f == 'MKT' else f}", f"{p3['coef'][f]:.2f} (t {p3['t'][f]:.2f})", f"{o3[f]['coef']:.2f} (t {o3[f]['t']:.2f})",
                     f"{r3[f]['coef']:.2f} (t {r3[f]['t']:.2f})"))
    rows.append(("R squared", pct(p3["r2"], 0), pct(o3["r2"], 0), pct(r3["r2"], 0)))
    q = h["aqr_original_table3_quarterly"]
    rows.append(("Alpha a quarter (Table 3 A)", f"{pct(paper.TABLE3_QUARTERLY['coef']['const'])} (t {paper.TABLE3_QUARTERLY['t']['const']:.2f})",
                 f"{pct(q['const']['coef'])} (t {q['const']['t']:.2f})", ""))
    s, so = h["aqr_original_straddle"], h["ours_paper_straddle"]
    rows.append(("Beta on market squared, quarterly (Table 3 C)", f"{paper.TABLE3_STRADDLE['coef']['MKT2']:.2f} (t {paper.TABLE3_STRADDLE['t']['MKT2']:.2f})",
                 f"{s['MKT2']['coef']:.2f} (t {s['MKT2']['t']:.2f})", f"{so['MKT2']['coef']:.2f} (t {so['MKT2']['t']:.2f})"))
    rows.append(("Alpha t, 12 month look back, 1 month hold (Table 2 A)", f"{paper.TABLE2_T_12_1:.2f}", "", f"{h['grid']['t_12_1']:.2f}"))
    rows.append(("Instruments with positive TSMOM Sharpe", f"{paper.N_POSITIVE} of {paper.N_INSTRUMENTS}", "",
                 f"{h['per_instrument']['positive']} of {h['per_instrument']['n']}"))
    rows.append(("Instruments significant at 5%", f"{paper.N_SIGNIFICANT} of {paper.N_INSTRUMENTS}", "",
                 f"{h['per_instrument']['significant_5pct']} of {h['per_instrument']['n']}"))
    t1 = pd.DataFrame(rows, columns=["1985 to 2009", "Paper", "AQR file of the paper's factor", "Our rebuild (public data)"])
    t1.to_csv(OUT / "table1_replication.csv", index=False)
    (OUT / "table1_replication.md").write_text(t1.to_markdown(index=False) + "\n")

    def row(name, s):
        return (name, s["first"] + " to " + s["last"], pct(s["mean_ann"] / 12), f"{s['t_nw']:.2f}", f"{s['sharpe']:.2f}",
                f"{s['sharpe_lo']:.2f} to {s['sharpe_hi']:.2f}", pct(s["max_drawdown"], 1))
    rows = [row("AQR factor, paper window (original file)", h["aqr_original"]),
            row("Our rebuild, paper window, gross", h["ours_paper"])]
    for c in COSTS_BP:
        rows.append(row(f"Our rebuild, paper window, net of {c:g} bp", h["net"][f"{c:g}bp"]))
    rows += [row("AQR factor, after the paper (updated file)", h["aqr_updated_oos"]),
             row("Our rebuild, after the paper, gross", h["ours_oos"]),
             row("Our rebuild, after the paper, net of 2 bp", h["ours_oos_net_2bp"])]
    t2 = pd.DataFrame(rows, columns=["Series", "Months", "Mean a month", "NW t (12 lags)", "Sharpe", "95% block bootstrap CI", "Max drawdown"])
    t2.to_csv(OUT / "table2_stress_out_of_sample.csv", index=False)
    (OUT / "table2_stress_out_of_sample.md").write_text(t2.to_markdown(index=False) + "\n")
    g = grid_t.copy()
    g.index.name = "look back \\ hold"
    (OUT / "table3_grid_alpha_t.md").write_text(g.round(2).to_markdown() + "\n")


def _charts(orig, upd, ours, lag_table) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for s, label, st_ in ((orig["TSMOM"], "AQR factor, original paper file", "-"), (upd["TSMOM"], "AQR factor, updated file", "--"),
                          (window(ours, "1985-01", OOS[1]), "Our rebuild, public data", "-")):
        s = s.dropna()
        label = f"{label} ({np.sqrt(12) * s.std():.0%} volatility)"
        ax.plot(s.index.to_timestamp(), np.cumprod(1 + s), st_, label=label)
    ax.axvline(pd.Timestamp("2010-01-01"), color="grey", lw=0.8)
    ax.set_yscale("log")
    ax.text(0.61, 0.05, "after the paper's sample", color="grey", transform=ax.transAxes)
    ax.set_ylabel("Growth of $1 (log scale, excess returns)")
    ax.set_title("12 month time series momentum, 40% volatility per position, 1985 to 2026")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "cumulative_returns.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, col, title in zip(axes, ["return", "sign"], ["Lagged scaled return (eq. 2)", "Sign of lagged return (eq. 3)"]):
        ax.bar(lag_table.index, lag_table[col], color=["#2b6cb0" if v > 0 else "#c05621" for v in lag_table[col]])
        ax.axhline(1.96, color="grey", lw=0.6, ls="--")
        ax.axhline(-1.96, color="grey", lw=0.6, ls="--")
        ax.set_title(title)
        ax.set_xlabel("Lag (months)")
    axes[0].set_ylabel("t statistic, clustered by month")
    fig.suptitle("Our rebuild of the paper's Fig. 1, 1985 to 2009")
    fig.tight_layout()
    fig.savefig(OUT / "lag_tstats_paper_fig1.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
