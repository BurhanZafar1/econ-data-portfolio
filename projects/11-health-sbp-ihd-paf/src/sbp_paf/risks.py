"""Relative risk inputs and their sampling distributions.

Main relative risks: Prospective Studies Collaboration (Lewington et al., Lancet
2002), hazard ratios for IHD death per 20 mmHg LOWER usual SBP, by age band, for
both sexes and by sex. They are log linear in SBP down to at least 115 mmHg.

Sensitivity: Ettehad et al. (Lancet 2016) trial meta analysis, relative risk of
coronary heart disease EVENTS 0.83 (0.78 to 0.88) per 10 mmHg SBP reduction.

Every cell carries a 'source' key naming the published estimate it uses, so that
cells sharing one estimate also share its random draw.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from sbp_paf import AGE_LABELS

Z975 = 1.959963984540054
# NHANES age groups map to PSC bands; 80+ uses the 80-89 band.
AGE_TO_PSC_BAND: dict[str, str] = {label: label for label in AGE_LABELS[:-1]} | {"80+": "80-89"}

# GBD 2019 theoretical minimum risk exposure level for SBP: uniform 110 to 115 mmHg.
TMREL_LOW, TMREL_HIGH = 110.0, 115.0

ETTEHAD_RR_PER_10 = (0.83, 0.78, 0.88)


def log_slope_from_hr(hr_per_20_lower: float) -> float:
    """Log relative risk per 1 mmHg HIGHER SBP implied by a hazard ratio per 20 mmHg LOWER SBP."""
    return -np.log(hr_per_20_lower) / 20.0


def log_se_from_ci(lower: float, upper: float) -> float:
    """Standard error on the log scale implied by a symmetric 95% interval on the ratio scale."""
    return (np.log(upper) - np.log(lower)) / (2.0 * Z975)


def load_psc(path: Path, sex_specific: bool = True) -> pd.DataFrame:
    """PSC table mapped to analysis cells: one row per (sex, age_group) with slope and its SE.

    Slopes are per 1 mmHg higher SBP; the SE is for log HR per 20 mmHg, divided by 20.
    """
    psc = pd.read_csv(path)
    rows = []
    for sex in ("Male", "Female"):
        source_sex = sex if sex_specific else "Both"
        for age, band in AGE_TO_PSC_BAND.items():
            rec = psc[(psc["sex"] == source_sex) & (psc["age_band"] == band)].iloc[0]
            rows.append(
                {
                    "sex": sex,
                    "age_group": age,
                    "source": f"PSC {source_sex} {band}",
                    "hr_per_20": rec["hr_per_20"],
                    "beta": log_slope_from_hr(rec["hr_per_20"]),
                    "beta_se": log_se_from_ci(rec["lower"], rec["upper"]) / 20.0,
                }
            )
    return pd.DataFrame(rows)


def ettehad_cells() -> pd.DataFrame:
    """Same layout as load_psc, with one trial based slope for every cell."""
    rr, lower, upper = ETTEHAD_RR_PER_10
    beta = -np.log(rr) / 10.0
    se = log_se_from_ci(lower, upper) / 10.0
    cells = [{"sex": s, "age_group": a, "source": "Ettehad 2016", "hr_per_20": rr**2, "beta": beta, "beta_se": se}
             for s in ("Male", "Female") for a in AGE_LABELS]
    return pd.DataFrame(cells)


def draw_tmrel(n_draws: int, rng: np.random.Generator) -> np.ndarray:
    """One TMREL per draw, uniform on [110, 115] mmHg and shared by all cells."""
    return rng.uniform(TMREL_LOW, TMREL_HIGH, n_draws)
