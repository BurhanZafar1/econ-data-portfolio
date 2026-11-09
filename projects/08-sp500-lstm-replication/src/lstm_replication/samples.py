"""The two samples: the paper window and the out of sample extension."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import data, features, splits


@dataclass
class Sample:
    table: pd.DataFrame  # features, fwd_return, label
    n_train: int

    @property
    def train(self) -> pd.DataFrame:
        return self.table.iloc[: self.n_train]

    @property
    def test(self) -> pd.DataFrame:
        return self.table.iloc[self.n_train :]


def paper_sample(raw: pd.DataFrame) -> Sample:
    """1 Jan 1980 to 28 Feb 2019, features built only from data inside the window, last 10% held out."""
    table = features.build(data.window(raw, data.PAPER_START, data.PAPER_END))
    n_train, _ = splits.holdout_sizes(len(table))
    return Sample(table, n_train)


def extension_sample(raw: pd.DataFrame) -> Sample:
    """Train on every paper row; test on days from 1 Mar 2019 on whose 21 day label is complete.

    Every training label ends by 27 Feb 2019 and every test label starts after it, so the
    two sets share no returns.
    """
    train = paper_sample(raw).table
    full = features.build(raw)
    test = full.loc[full.index >= pd.Timestamp("2019-03-01")]
    return Sample(pd.concat([train, test]), len(train))
