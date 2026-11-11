"""Survey design tools for NHANES: Taylor linearized variance and Rao-Wu bootstrap weights.

The bootstrap resamples PSUs within strata (Rao and Wu 1988) with m_h = n_h - 1
PSUs drawn per stratum and weights multiplied by (n_h / m_h) times the number
of times each PSU is drawn. Each replicate is one plausible draw of the exposure
distribution, so sampling uncertainty in SBP flows into every PAF draw.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rao_wu_weights(design: pd.DataFrame, n_reps: int, rng: np.random.Generator,
                   weight: str = "wt_mec", stratum: str = "stratum", psu: str = "psu") -> np.ndarray:
    """Replicate weights, shape (n_rows, n_reps)."""
    multipliers = np.zeros((len(design), n_reps))
    strata = design[stratum].to_numpy()
    psus = design[psu].to_numpy()
    for h in np.unique(strata):
        in_h = strata == h
        labels = np.unique(psus[in_h])
        n_h = len(labels)
        if n_h < 2:
            raise ValueError(f"Stratum {h} has {n_h} PSU; the bootstrap needs at least 2.")
        m_h = n_h - 1
        picks = rng.integers(0, n_h, size=(m_h, n_reps))
        counts = np.stack([(picks == j).sum(axis=0) for j in range(n_h)])  # (n_h, n_reps)
        for j, label in enumerate(labels):
            rows = in_h & (psus == label)
            multipliers[rows] = (n_h / m_h) * counts[j]
    return design[weight].to_numpy()[:, None] * multipliers


def taylor_se_mean(y: np.ndarray, w: np.ndarray, domain: np.ndarray,
                   strata: np.ndarray, psus: np.ndarray) -> tuple[float, float]:
    """Weighted domain mean and its Taylor linearized standard error (with replacement PSUs)."""
    d = domain.astype(float)
    total_w = (w * d).sum()
    mean = (w * d * y).sum() / total_w
    z = w * d * (y - mean) / total_w
    frame = pd.DataFrame({"z": z, "h": strata, "p": psus})
    psu_tot = frame.groupby(["h", "p"])["z"].sum().reset_index()
    var = 0.0
    for _, grp in psu_tot.groupby("h"):
        n_h = len(grp)
        var += n_h / (n_h - 1) * ((grp["z"] - grp["z"].mean()) ** 2).sum()
    return float(mean), float(np.sqrt(var))
