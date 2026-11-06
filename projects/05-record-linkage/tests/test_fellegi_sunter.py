"""The Fellegi-Sunter model: a hand calculation and recovery of known parameters."""

import numpy as np
import pandas as pd
import pytest

from linkage.fellegi_sunter import FellegiSunter, fit

SEED = 20261106


def test_posterior_and_weight_by_hand():
    # Two binary fields. Pair agrees on field x, disagrees on y, z missing.
    model = FellegiSunter(match_share=0.1,
                          m={"x": np.array([0.1, 0.9]), "y": np.array([0.2, 0.8]),
                             "z": np.array([0.5, 0.5])},
                          u={"x": np.array([0.8, 0.2]), "y": np.array([0.9, 0.1]),
                             "z": np.array([0.5, 0.5])},
                          iterations=0, log_likelihood=0.0)
    levels = pd.DataFrame({"x": [1.0], "y": [0.0], "z": [np.nan]})
    # weight = log2(0.9/0.2) + log2(0.2/0.9) = 0 bits, so posterior = prior = 0.1.
    assert model.match_weight(levels).iloc[0] == pytest.approx(0.0)
    assert model.posterior(levels).iloc[0] == pytest.approx(0.1)
    levels = pd.DataFrame({"x": [1.0], "y": [1.0], "z": [np.nan]})
    numerator = 0.1 * 0.9 * 0.8
    expected = numerator / (numerator + 0.9 * 0.2 * 0.1)
    assert model.posterior(levels).iloc[0] == pytest.approx(expected)


def simulate(n_pairs: int, share: float, m: dict, u: dict, missing: float,
             rng: np.random.Generator) -> pd.DataFrame:
    is_match = rng.random(n_pairs) < share
    columns = {}
    for field in m:
        k = len(m[field])
        draws = np.where(is_match, rng.choice(k, n_pairs, p=m[field]),
                         rng.choice(k, n_pairs, p=u[field])).astype(float)
        draws[rng.random(n_pairs) < missing] = np.nan
        columns[field] = draws
    return pd.DataFrame(columns)


def test_em_recovers_simulated_parameters():
    rng = np.random.default_rng(SEED)
    m = {"name": np.array([0.05, 0.10, 0.85]), "dob": np.array([0.05, 0.05, 0.90]),
         "street": np.array([0.15, 0.85]), "city": np.array([0.10, 0.10, 0.80])}
    u = {"name": np.array([0.90, 0.07, 0.03]), "dob": np.array([0.95, 0.04, 0.01]),
         "street": np.array([0.97, 0.03]), "city": np.array([0.70, 0.20, 0.10])}
    levels = simulate(60_000, 0.15, m, u, missing=0.05, rng=rng)
    model = fit(levels, {f: len(p) for f, p in m.items()})
    assert model.match_share == pytest.approx(0.15, abs=0.005)
    for field in m:
        np.testing.assert_allclose(model.m[field], m[field], atol=0.015)
        np.testing.assert_allclose(model.u[field], u[field], atol=0.015)


def test_em_never_lowers_likelihood_and_converges():
    rng = np.random.default_rng(SEED + 1)
    m = {"a": np.array([0.1, 0.9]), "b": np.array([0.2, 0.8]), "c": np.array([0.1, 0.9])}
    u = {"a": np.array([0.9, 0.1]), "b": np.array([0.7, 0.3]), "c": np.array([0.8, 0.2])}
    levels = simulate(5_000, 0.3, m, u, missing=0.0, rng=rng)
    short = fit(levels, {f: 2 for f in m}, max_iterations=3)
    full = fit(levels, {f: 2 for f in m})
    assert full.log_likelihood >= short.log_likelihood
    assert full.iterations < 1000
