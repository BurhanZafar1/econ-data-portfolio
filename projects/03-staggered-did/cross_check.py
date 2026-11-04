"""Optional: compare this project with independent packages, then exit.

Not needed to run the project. Install the extra packages first:
    pip install moderndid==0.4.1 pyfixest==0.60.0 polars==2.1.0
Requires Python 3.11 or newer and its own virtual environment, since these
packages need newer library versions than requirements.txt pins.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import moderndid  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import polars as pl  # noqa: E402
import pyfixest  # noqa: E402

from staggered_did.aggregate import event_study, group_att, simple_att  # noqa: E402
from staggered_did.group_time import estimate_group_time  # noqa: E402
from staggered_did.inference import standard_errors  # noqa: E402
from staggered_did.panel import load_minimum_wage  # noqa: E402
from staggered_did.twfe import static_twfe  # noqa: E402

DATA = ROOT / "data" / "mpdta.csv"
TOLERANCE = 1e-7


def report(name: str, ours: np.ndarray, theirs: np.ndarray) -> None:
    gap = float(np.max(np.abs(np.asarray(ours) - np.asarray(theirs))))
    print(f"{name:45s} largest gap {gap:.1e}")
    if gap > TOLERANCE:
        raise SystemExit(f"{name} differs from the reference package")


def package_fit(frame: pl.DataFrame, **options: object) -> object:
    return moderndid.att_gt(
        data=frame, yname="lemp", tname="year", idname="countyreal",
        gname="first.treat", est_method="reg", boot=False, **options,
    )


def main() -> None:
    raw = pd.read_csv(DATA).astype({"first.treat": int, "countyreal": int})
    frame = pl.from_pandas(raw)
    panel = load_minimum_wage(DATA)
    adjusted = load_minimum_wage(DATA, ("lpop",))

    cases = [
        ("never treated", estimate_group_time(panel), package_fit(frame)),
        (
            "not yet treated",
            estimate_group_time(panel, control="notyet"),
            package_fit(frame, control_group="notyettreated"),
        ),
        (
            "log population",
            estimate_group_time(adjusted),
            package_fit(frame, xformla="~lpop"),
        ),
    ]
    for name, ours, theirs in cases:
        report(f"ATT(g,t), {name}", ours.table["att"].to_numpy(), theirs.att_gt)
        report(f"SE of ATT(g,t), {name}", standard_errors(ours.influence), theirs.se_gt)

    main_ours, main_theirs = cases[0][1], cases[0][2]
    for kind, aggregate in (
        ("simple", simple_att), ("group", group_att), ("dynamic", event_study),
    ):
        ours = aggregate(main_ours)
        theirs = moderndid.aggte(main_theirs, type=kind)
        report(f"overall {kind}", ours.estimate[-1], theirs.overall_att)
        report(f"SE overall {kind}", standard_errors(ours.influence)[-1], theirs.overall_se)

    raw["state"] = raw["countyreal"] // 1000
    raw["post"] = ((raw["first.treat"] > 0) & (raw["year"] >= raw["first.treat"])).astype(int)
    fit = static_twfe(panel)
    for cluster, se in (("countyreal", fit.se_unit), ("state", fit.se_cluster)):
        reference = pyfixest.feols(
            "lemp ~ post | countyreal + year", data=raw, vcov={"CRV1": cluster}
        ).tidy()
        report(f"TWFE coefficient, {cluster}", fit.coef, reference["Estimate"].to_numpy())
        report(f"TWFE SE, {cluster}", se, reference["Std. Error"].to_numpy())
    print("All comparisons agree.")


if __name__ == "__main__":
    main()
