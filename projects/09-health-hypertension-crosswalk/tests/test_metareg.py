"""Known answer: the BCG vaccine trials (Colditz et al. 1994), the standard meta-analysis example.

Published DerSimonian and Laird results (metafor documentation; Viechtbauer
2010, J Stat Softw 36(3)): pooled log relative risk -0.7141 (SE 0.1787) with
tau^2 = 0.3088; with absolute latitude as moderator, intercept 0.2595
(SE 0.2323), slope -0.0292 (SE 0.0067) and tau^2 = 0.0633.
"""

import numpy as np
import pytest

from htn_crosswalk.metareg import fit_dl

# trial: treated TB cases, treated non cases, control cases, control non cases, absolute latitude
BCG = np.array(
    [
        [4, 119, 11, 128, 44], [6, 300, 29, 274, 55], [3, 228, 11, 209, 42],
        [62, 13536, 248, 12619, 52], [33, 5036, 47, 5761, 13], [180, 1361, 372, 1079, 44],
        [8, 2537, 10, 619, 19], [505, 87886, 499, 87892, 13], [29, 7470, 45, 7232, 27],
        [17, 1699, 65, 1600, 42], [186, 50448, 141, 27197, 18], [5, 2493, 3, 2338, 33],
        [27, 16886, 29, 17825, 33],
    ],
    dtype=float,
)


def _log_rr() -> tuple[np.ndarray, np.ndarray]:
    a, b, c, d = BCG[:, 0], BCG[:, 1], BCG[:, 2], BCG[:, 3]
    yi = np.log((a / (a + b)) / (c / (c + d)))
    vi = 1 / a - 1 / (a + b) + 1 / c - 1 / (c + d)
    return yi, vi


def test_bcg_random_effects_pooled():
    yi, vi = _log_rr()
    fit = fit_dl(yi, vi, np.ones((13, 1)), ("intercept",))
    assert fit.beta[0] == pytest.approx(-0.7141, abs=5e-5)
    assert fit.se[0] == pytest.approx(0.1787, abs=5e-5)
    assert fit.tau2 == pytest.approx(0.3088, abs=5e-5)
    assert fit.q_e == pytest.approx(152.2330, abs=5e-4)


def test_bcg_meta_regression_on_latitude():
    yi, vi = _log_rr()
    x = np.column_stack([np.ones(13), BCG[:, 4]])
    fit = fit_dl(yi, vi, x, ("intercept", "ablat"))
    np.testing.assert_allclose(fit.beta, [0.259544, -0.029229], atol=5e-6)
    np.testing.assert_allclose(fit.se, [0.232307, 0.006733], atol=5e-6)
    assert fit.tau2 == pytest.approx(0.063301, abs=5e-6)


def test_no_heterogeneity_gives_fixed_effect():
    y = np.array([1.0, 1.0, 1.0, 1.0])
    fit = fit_dl(y, np.full(4, 0.1), np.ones((4, 1)), ("intercept",))
    assert fit.tau2 == 0.0
    assert fit.se[0] == pytest.approx(np.sqrt(0.1 / 4))
