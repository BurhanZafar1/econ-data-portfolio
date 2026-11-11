"""Population attributable fraction for a continuous exposure.

For exposure x with density P(x), relative risk RR(x) and a counterfactual
distribution at the theoretical minimum risk exposure level (TMREL):

    PAF = (integral RR(x) P(x) dx - RR(TMREL)) / integral RR(x) P(x) dx

(the comparative risk assessment formula used in GBD 2019).
With RR(x) = exp(beta * max(x - TMREL, 0)), RR(TMREL) = 1. The integral is
replaced by the survey weighted mean of RR over sampled people, so the exposure
distribution is the empirical, design weighted one; no parametric shape is assumed.
"""

from __future__ import annotations

import numpy as np


def relative_risk(sbp: np.ndarray, beta: np.ndarray | float, tmrel: np.ndarray | float) -> np.ndarray:
    """RR relative to the TMREL; 1 at or below the TMREL, log linear above it.

    Broadcasting lets sbp be (n, 1) and beta, tmrel be (n_draws,).
    """
    excess = np.maximum(np.asarray(sbp) - tmrel, 0.0)
    return np.exp(np.asarray(beta) * excess)


def paf_from_mean_rr(mean_rr: np.ndarray | float) -> np.ndarray:
    """PAF from the population mean relative risk (counterfactual RR is 1)."""
    mean_rr = np.asarray(mean_rr, dtype=float)
    return (mean_rr - 1.0) / mean_rr


def weighted_paf(sbp: np.ndarray, weights: np.ndarray, beta: np.ndarray | float,
                 tmrel: np.ndarray | float) -> np.ndarray:
    """PAF from individual SBP values and weights.

    sbp: (n,). weights: (n,) or (n, d). beta, tmrel: scalars or (d,).
    Returns a scalar or a (d,) vector of PAFs, one per draw.
    """
    rr = relative_risk(sbp[:, None], beta, tmrel)  # (n, d) or (n, 1)
    w = weights if weights.ndim == 2 else weights[:, None]
    mean_rr = (w * rr).sum(axis=0) / w.sum(axis=0)
    out = paf_from_mean_rr(mean_rr)
    return out if out.size > 1 else out.item()


def normal_paf_closed_form(mu: float, sigma: float, beta: float, tmrel: float) -> float:
    """Exact PAF for x ~ Normal(mu, sigma) with RR = exp(beta * (x - tmrel)) on the whole line.

    No truncation at the TMREL, so E[RR] = exp(beta * (mu - tmrel) + beta^2 sigma^2 / 2).
    Used only as a known answer check of the numerical integration.
    """
    mean_rr = np.exp(beta * (mu - tmrel) + 0.5 * beta**2 * sigma**2)
    return float(paf_from_mean_rr(mean_rr))


def levin_paf(prevalence: float, rr: float) -> float:
    """Levin's formula for a binary exposure, p (RR - 1) / (1 + p (RR - 1))."""
    excess = prevalence * (rr - 1.0)
    return excess / (1.0 + excess)
