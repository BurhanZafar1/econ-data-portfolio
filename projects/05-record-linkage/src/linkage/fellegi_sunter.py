"""Fellegi-Sunter model fitted by EM, with no labeled data.

Each candidate pair is either a match (M) or a non-match (U). Given the class,
fields agree independently:
    m_k(l) = P(field k at level l | M),   u_k(l) = P(field k at level l | U).
With lambda = P(M), the likelihood of comparison vector g is
    lambda * prod_k m_k(g_k) + (1 - lambda) * prod_k u_k(g_k).
EM alternates between the posterior match probability of every pair (E step)
and weighted level frequencies (M step), as in Jaro (1989). Missing
comparisons drop out of the product (Enamorado, Fifield and Imai 2019).

The match weight of a pair is sum_k log2(m_k(g_k) / u_k(g_k)) (Fellegi and
Sunter 1969); the posterior is a monotone function of it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

TOLERANCE = 1e-10
MAX_ITERATIONS = 1000
PROBABILITY_FLOOR = 1e-9


@dataclass
class FellegiSunter:
    """Fitted parameters: P(M), and per field the m and u level probabilities.

    log_likelihood is evaluated at the last E step, one update before the
    stored parameters; at convergence the two differ by less than the tolerance.
    """

    match_share: float
    m: dict[str, np.ndarray]
    u: dict[str, np.ndarray]
    iterations: int
    log_likelihood: float

    def log2_ratios(self, levels: pd.DataFrame) -> pd.DataFrame:
        """Per field log2(m/u) at each pair's level; zero where the level is missing."""
        out = {}
        for field in self.m:
            column = levels[field].to_numpy()
            ratio = np.log2(self.m[field]) - np.log2(self.u[field])
            observed = ~np.isnan(column)
            values = np.zeros(len(column))
            values[observed] = ratio[column[observed].astype(int)]
            out[field] = values
        return pd.DataFrame(out, index=levels.index)

    def match_weight(self, levels: pd.DataFrame) -> pd.Series:
        """Total Fellegi-Sunter match weight in bits."""
        return self.log2_ratios(levels).sum(axis=1).rename("match_weight")

    def posterior(self, levels: pd.DataFrame) -> pd.Series:
        """P(match | comparison vector) by Bayes' rule."""
        prior_odds_bits = np.log2(self.match_share) - np.log2(1 - self.match_share)
        bits = self.match_weight(levels).to_numpy() + prior_odds_bits
        return pd.Series(1 / (1 + np.exp2(-bits)), index=levels.index, name="posterior")


def _level_probabilities(column: np.ndarray, weights: np.ndarray, n_levels: int) -> np.ndarray:
    """Weighted share of each level among pairs where the field is observed."""
    observed = ~np.isnan(column)
    counts = np.bincount(column[observed].astype(int), weights=weights[observed],
                         minlength=n_levels)
    shares = counts / counts.sum()
    shares = np.clip(shares, PROBABILITY_FLOOR, None)
    return shares / shares.sum()


def _log_class_likelihood(levels: pd.DataFrame, probabilities: dict[str, np.ndarray]) -> np.ndarray:
    """Sum over observed fields of log P(level | class), one value per pair."""
    total = np.zeros(len(levels))
    for field, probs in probabilities.items():
        column = levels[field].to_numpy()
        observed = ~np.isnan(column)
        total[observed] += np.log(probs[column[observed].astype(int)])
    return total


def _starting_values(n_levels: int, top_share: float) -> np.ndarray:
    """Probability top_share on the top level, the rest spread evenly below it."""
    start = np.full(n_levels, (1 - top_share) / (n_levels - 1))
    start[-1] = top_share
    return start


def fit(levels: pd.DataFrame, n_levels: dict[str, int], match_share: float = 0.1,
        tolerance: float = TOLERANCE, max_iterations: int = MAX_ITERATIONS) -> FellegiSunter:
    """Estimate lambda, m and u by EM from unlabeled comparison levels.

    Starting values put most m mass on 'agree' and most u mass on 'disagree',
    which fixes which latent class is called the match class.
    """
    m = {f: _starting_values(k, 0.9) for f, k in n_levels.items()}
    u = {f: _starting_values(k, 0.1) for f, k in n_levels.items()}
    previous = -np.inf
    for iteration in range(1, max_iterations + 1):
        log_match = np.log(match_share) + _log_class_likelihood(levels, m)
        log_non_match = np.log(1 - match_share) + _log_class_likelihood(levels, u)
        log_total = np.logaddexp(log_match, log_non_match)
        responsibility = np.exp(log_match - log_total)
        log_likelihood = float(log_total.sum())

        match_share = float(responsibility.mean())
        for field, k in n_levels.items():
            column = levels[field].to_numpy()
            m[field] = _level_probabilities(column, responsibility, k)
            u[field] = _level_probabilities(column, 1 - responsibility, k)
        if log_likelihood - previous < tolerance:
            break
        previous = log_likelihood
    return FellegiSunter(match_share, m, u, iteration, log_likelihood)


def parameter_table(model: FellegiSunter) -> pd.DataFrame:
    """m, u and the agreement weight log2(m/u) for every field and level."""
    rows = []
    for field in model.m:
        for level, (m_value, u_value) in enumerate(zip(model.m[field], model.u[field])):
            rows.append({"field": field, "level": level, "m": m_value, "u": u_value,
                         "weight_bits": float(np.log2(m_value / u_value))})
    return pd.DataFrame(rows)
