import numpy as np

from pairs import trading

# Hand computed example. Threshold 2 x 0.02 = 0.04.
# day 1: a +10% -> spread 0.10 > 0.04: short a, long b
# day 2: a -5%  -> short leg worth 0.95, value 1.05
# day 3: a -6%  -> prices cross (spread < 0): close, short leg 0.95 x 0.94 = 0.893
RA = np.array([[0.0], [0.10], [-0.05], [-0.06]])
RB = np.zeros((4, 1))
SIGMA = np.array([0.02])


def test_hand_computed_no_wait():
    res = trading.simulate(RA, RB, SIGMA, k=2.0, wait=0)
    assert np.allclose(res.value[:, 0], [1.0, 1.0, 1.05, 1.107])
    assert res.round_trips[0] == 1 and res.opened[0]


def test_hand_computed_wait_one_day():
    # signal day 1, open at the close of day 2, so only day 3's move counts; forced close at the end
    res = trading.simulate(RA, RB, SIGMA, k=2.0, wait=1)
    assert np.allclose(res.value[:, 0], [1.0, 1.0, 1.0, 1.06])


def test_costs_are_charged_per_leg_per_side():
    c = 0.001
    res = trading.simulate(RA, RB, SIGMA, k=2.0, wait=0, cost=c)
    expected = 1.0 - 2 * c + (1.0 - 0.893) - c * (1.0 + 0.893)
    assert np.isclose(res.value[-1, 0], expected)


def test_never_opens_inside_band():
    ra = np.full((50, 1), 0.001)
    rb = np.full((50, 1), 0.001)
    res = trading.simulate(ra, rb, np.array([0.05]))
    assert not res.opened[0] and np.allclose(res.value, 1.0)


def test_no_look_ahead():
    rng = np.random.default_rng(4)
    ra, rb = rng.normal(0, 0.02, (126, 30)), rng.normal(0, 0.02, (126, 30))
    sigma = np.full(30, 0.03)
    for wait in (0, 1):
        base = trading.simulate(ra, rb, sigma, wait=wait).value
        for t in (10, 60, 100):
            ra2, rb2 = ra.copy(), rb.copy()
            ra2[t + 1 :] = rng.normal(0, 0.05, ra2[t + 1 :].shape)
            rb2[t + 1 :] = rng.normal(0, 0.05, rb2[t + 1 :].shape)
            alt = trading.simulate(ra2, rb2, sigma, wait=wait).value
            assert np.allclose(base[: t + 1], alt[: t + 1])


def test_delisting_closes_and_freezes():
    ra = RA.copy()
    ra = np.vstack([ra[:3], [[np.nan]], [[0.5]]])
    rb = np.zeros((5, 1))
    res = trading.simulate(ra, rb, SIGMA)
    assert np.allclose(res.value[2:, 0], 1.05)


def test_no_open_on_last_day():
    # divergence on the second to last day: with a one day wait the open would land on the
    # last day and close immediately, so it is skipped
    ra = np.array([[0.0], [0.0], [0.10], [0.0]])
    res = trading.simulate(ra, np.zeros((4, 1)), SIGMA, wait=1, cost=0.001)
    assert not res.opened[0] and np.allclose(res.value, 1.0)
