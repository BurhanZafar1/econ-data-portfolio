"""Formation period: normalized prices, distances and pair selection (GGR 2006, section 1.3).

Each security's normalized price is its cumulative total return index, starting at 1.
Each security is matched with the partner that minimizes the sum of squared deviations
(SSD) between the two normalized price series. The resulting set of distinct pairs is
ranked by SSD; the top 5 and top 20 are traded. Only formation period data are used.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def normalized_prices(returns: np.ndarray) -> np.ndarray:
    """Cumulative total return index (T x N) starting at 1 + r on the first day."""
    return np.cumprod(1.0 + returns, axis=0)


def ssd_matrix(prices: np.ndarray) -> np.ndarray:
    """N x N matrix of sums of squared deviations between normalized price columns."""
    sq = np.einsum("ti,ti->i", prices, prices)
    cross = prices.T @ prices
    d = sq[:, None] + sq[None, :] - 2.0 * cross
    d = np.maximum(d, 0.0)
    np.fill_diagonal(d, np.inf)
    return d


@dataclass(frozen=True)
class Pairs:
    """Selected pairs (column indices), ranked by SSD, and each pair's formation spread SD."""

    a: np.ndarray
    b: np.ndarray
    ssd: np.ndarray
    sigma: np.ndarray


def _spread_sd(prices: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (prices[:, a] - prices[:, b]).std(axis=0, ddof=1)


def nearest_neighbor_pairs(returns: np.ndarray) -> Pairs:
    """GGR selection: each security's minimum distance partner; distinct pairs ranked by SSD.

    returns: T x N formation period returns with no missing values.
    """
    prices = normalized_prices(returns)
    d = ssd_matrix(prices)
    partner = np.argmin(d, axis=1)
    edges = {(min(i, j), max(i, j)) for i, j in enumerate(partner)}
    a = np.array([e[0] for e in edges], dtype=int)
    b = np.array([e[1] for e in edges], dtype=int)
    dist = d[a, b]
    order = np.lexsort((b, a, dist))  # ties broken by index for determinism
    a, b, dist = a[order], b[order], dist[order]
    return Pairs(a, b, dist, _spread_sd(prices, a, b))


def all_pairs_ranked(returns: np.ndarray) -> Pairs:
    """Robustness variant: every one of the N(N-1)/2 pairs ranked by SSD."""
    prices = normalized_prices(returns)
    d = ssd_matrix(prices)
    a, b = np.triu_indices(d.shape[0], k=1)
    dist = d[a, b]
    order = np.lexsort((b, a, dist))
    a, b, dist = a[order], b[order], dist[order]
    return Pairs(a, b, dist, _spread_sd(prices, a, b))


def random_pairs(n_assets: int, n_pairs: int, rng: np.random.Generator, returns: np.ndarray) -> Pairs:
    """Placebo: pairs drawn at random (no distance information), same trading rule."""
    prices = normalized_prices(returns)
    a = np.empty(n_pairs, dtype=int)
    b = np.empty(n_pairs, dtype=int)
    for k in range(n_pairs):
        a[k], b[k] = rng.choice(n_assets, size=2, replace=False)
    return Pairs(a, b, np.full(n_pairs, np.nan), _spread_sd(prices, a, b))
