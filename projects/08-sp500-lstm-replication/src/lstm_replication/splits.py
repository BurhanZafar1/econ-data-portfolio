"""Hold out split and walk forward validation, with and without purging.

The original project used scikit-learn's train_test_split(test_size=0.1, shuffle=False)
and TimeSeriesSplit with 8 folds. Because each label spans the next 21 trading days,
the last 21 training labels of every fold overlap the first validation days. A purged
split (Lopez de Prado 2018, ch. 7) drops those training rows.
"""

from __future__ import annotations

import math
from collections.abc import Iterator

import numpy as np
from sklearn.model_selection import TimeSeriesSplit

TEST_FRACTION = 0.1
# The notebook set n_splits = int((1 // 0.1) - 1). In floating point 1 // 0.1 equals 9.0,
# so this is 8 folds, not the 9 one might expect.
N_SPLITS = int((1 // 0.1) - 1)


def holdout_sizes(n: int, test_fraction: float = TEST_FRACTION) -> tuple[int, int]:
    """Train and test sizes used by train_test_split with a float test_size (test rounds up)."""
    n_test = math.ceil(test_fraction * n)
    return n - n_test, n_test


def walk_forward(n: int, n_splits: int = N_SPLITS) -> list[tuple[np.ndarray, np.ndarray]]:
    """The original, unpurged expanding window folds."""
    return list(TimeSeriesSplit(n_splits=n_splits).split(np.arange(n)))


def purged_walk_forward(
    n: int, n_splits: int = N_SPLITS, purge: int = 21
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Same folds, keeping only training rows whose label window ends before validation.

    Row i's label uses returns i+1 .. i+purge. The first validation label uses returns
    from v0+1 onward, so a training row is clean when i + purge <= v0.
    """
    for train, valid in walk_forward(n, n_splits):
        keep = train[train + purge <= valid[0]]
        yield keep, valid
