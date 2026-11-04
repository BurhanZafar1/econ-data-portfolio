"""Simulated check with a known truth: effects that grow after treatment.

Nothing here is real data. It exists to show, on a design where the right
answer is known, the failure that TWFE has and group time estimators do not.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from staggered_did.aggregate import simple_att
from staggered_did.group_time import estimate_group_time
from staggered_did.inference import standard_errors
from staggered_did.panel import Panel
from staggered_did.twfe import static_twfe

@dataclass(frozen=True)
class Design:
    """Timing of a simulated rollout. Cohort 0 means never treated."""

    name: str
    years: np.ndarray
    cohorts: np.ndarray
    shares: np.ndarray

# A deliberately hard case: long panel, nearly every unit eventually treated.
STRESS_TEST = Design(
    "stress test, 10 years, 90 percent treated",
    np.arange(2001, 2011),
    np.array([0, 2003, 2005, 2007]),
    np.array([0.1, 0.3, 0.3, 0.3]),
)
# The years and cohort shares of the real sample.
SAMPLE_SHAPED = Design(
    "sample shaped, 5 years, 38 percent treated",
    np.arange(2003, 2008),
    np.array([0, 2004, 2006, 2007]),
    np.array([309, 20, 40, 131]) / 500,
)
EFFECT_PER_YEAR = 0.05

def simulate_panel(
    design: Design, n_units: int, rng: np.random.Generator
) -> tuple[Panel, float]:
    """Draw one panel; return it with the true ATT over treated unit years.

    Units are independent, so this checks the estimators and unit level
    standard errors. It says nothing about inference with few treated states.
    """
    years = design.years
    cohort = rng.choice(design.cohorts, size=n_units, p=design.shares)
    unit_effect = rng.normal(0, 1, n_units)
    year_effect = 0.02 * (years - years[0])
    noise = rng.normal(0, 0.2, (n_units, years.size))
    ever = cohort > 0
    exposure = (years[None, :] - cohort[:, None] + 1) * ever[:, None]
    effect = EFFECT_PER_YEAR * np.clip(exposure, 0, None)
    y = unit_effect[:, None] + year_effect[None, :] + effect + noise
    panel = Panel(
        y=y, years=years, cohort=cohort,
        units=np.arange(n_units), clusters=np.arange(n_units),
    )
    return panel, float(effect[panel.treated == 1].mean())

def monte_carlo(design: Design, draws: int, n_units: int, seed: int) -> pd.DataFrame:
    """Compare TWFE and the group time simple ATT with the truth."""
    rng = np.random.default_rng(seed)
    records = []
    for _ in range(draws):
        panel, truth = simulate_panel(design, n_units, rng)
        group_time = estimate_group_time(panel)
        simple = simple_att(group_time)
        estimate = float(simple.estimate[0])
        se = float(standard_errors(simple.influence)[0])
        records.append({
            "truth": truth,
            "twfe": float(static_twfe(panel).coef[0]),
            "group_time": estimate,
            "covered": abs(estimate - truth) <= 1.96 * se,
        })
    frame = pd.DataFrame(records)
    return pd.DataFrame([{
        "design": design.name,
        "draws": draws,
        "n_units": n_units,
        "mean_truth": frame["truth"].mean(),
        "mean_twfe": frame["twfe"].mean(),
        "mean_group_time": frame["group_time"].mean(),
        "group_time_ci_coverage": frame["covered"].mean(),
    }])
