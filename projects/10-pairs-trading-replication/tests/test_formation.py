import numpy as np

from pairs import formation


def test_ssd_matches_brute_force():
    rng = np.random.default_rng(1)
    r = rng.normal(0, 0.01, (250, 6))
    p = formation.normalized_prices(r)
    d = formation.ssd_matrix(p)
    for i in range(6):
        for j in range(6):
            if i != j:
                assert np.isclose(d[i, j], ((p[:, i] - p[:, j]) ** 2).sum(), atol=1e-9)
    assert np.isinf(np.diag(d)).all()


def test_nearest_neighbor_picks_the_twin_first():
    rng = np.random.default_rng(2)
    r = rng.normal(0, 0.02, (250, 5))
    r[:, 3] = r[:, 1] + rng.normal(0, 0.0005, 250)  # 1 and 3 are near twins
    pairs = formation.nearest_neighbor_pairs(r)
    assert {pairs.a[0], pairs.b[0]} == {1, 3}
    assert np.all(np.diff(pairs.ssd) >= 0)
    # every security appears in at least one pair (it is matched with its nearest partner)
    assert set(pairs.a) | set(pairs.b) == set(range(5))


def test_spread_sigma_is_formation_spread_sd():
    rng = np.random.default_rng(3)
    r = rng.normal(0, 0.01, (120, 4))
    pairs = formation.all_pairs_ranked(r)
    p = formation.normalized_prices(r)
    a, b = pairs.a[0], pairs.b[0]
    assert np.isclose(pairs.sigma[0], (p[:, a] - p[:, b]).std(ddof=1))
    assert len(pairs.a) == 6
