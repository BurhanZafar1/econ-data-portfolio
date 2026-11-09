"""Known answer tests for the data pipeline, against the original notebook's printed outputs."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lstm_replication import data, features, paper, samples, splits

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "sp500_daily.csv"


@pytest.fixture(scope="module")
def raw():
    return data.load_raw(RAW)


def test_row_counts_match_notebook(raw):
    assert len(data.window(raw, data.PAPER_START, data.PAPER_END)) == paper.RAW_ROWS == 9875
    assert len(samples.paper_sample(raw).table) == paper.FEATURE_ROWS == 9454


def test_test_labels_match_notebook_exactly(raw):
    s = samples.paper_sample(raw)
    assert len(s.test) == 946 and s.n_train == 8508
    assert s.test["label"].mean() == pytest.approx(paper.TEST_UP_SHARE, abs=1e-15)


def test_training_labels_match_notebook_exactly(raw):
    s = samples.paper_sample(raw)
    assert s.train["label"].mean() == pytest.approx(paper.TRAIN_UP_SHARE, abs=1e-15)


def test_feature_table_dates_match_notebook(raw):
    table = samples.paper_sample(raw).table
    assert str(table.index[0].date()) == "1981-07-31"
    assert str(table.index[-1].date()) == "2019-01-28"


def test_feature_values_match_notebook_printout(raw):
    # The notebook printed these values for 31 July 1981.
    table = samples.paper_sample(raw).table
    row = table.loc["1981-07-31"]
    assert row["ret_1w"] == pytest.approx(0.018969, abs=1e-6)
    assert row["ret_8w"] == pytest.approx(-0.000306, abs=1e-6)
    assert row["volume_48w"] == pytest.approx(4.800596e7, rel=1e-6)


def test_hand_calculated_features_on_toy_series():
    close = pd.Series(np.exp(np.arange(500) * 0.01), index=pd.bdate_range("2000-01-03", periods=500))
    frame = pd.DataFrame({"close": close, "volume": np.full(500, 100.0)})
    table = features.build(frame)
    first = table.iloc[0]
    assert first["ret_1w"] == pytest.approx(0.05)  # 5 days of 0.01
    assert first["ret_80w"] == pytest.approx(4.0)  # 400 days of 0.01
    assert first["vol_4w"] == pytest.approx(0.0, abs=1e-12)  # constant returns
    assert first["volume_12w"] == pytest.approx(100.0)
    assert first["fwd_return"] == pytest.approx(0.21)  # next 21 days
    assert len(table) == 500 - 400 - 21  # 400 day window, 21 day label


def test_label_uses_only_future_returns():
    r = pd.Series([0.0, 1.0, -1.0, 2.0, 0.5])
    fwd = features.forward_return(r, horizon=2)
    assert fwd.iloc[1] == pytest.approx(-1.0 + 2.0)  # r2 + r3
    assert fwd.iloc[2] == pytest.approx(2.0 + 0.5)  # r3 + r4
    assert np.isnan(fwd.iloc[3])  # not enough future returns


def test_holdout_sizes_follow_train_test_split():
    assert splits.holdout_sizes(9454) == (8508, 946)


def test_purged_folds_have_no_label_overlap():
    assert splits.N_SPLITS == 8  # int((1 // 0.1) - 1), as the notebook computed it
    for train, valid in splits.purged_walk_forward(8508, purge=21):
        assert train.max() + 21 <= valid[0]
    original = splits.walk_forward(8508)
    assert original[0][0].max() + 1 == original[0][1][0]  # the original folds touch


def test_extension_shares_no_returns_with_training(raw):
    ext = samples.extension_sample(raw)
    last_train_label_end = raw.index[raw.index.get_loc(ext.train.index[-1]) + 21]
    assert last_train_label_end <= pd.Timestamp("2019-02-27")
    assert ext.test.index[0] >= pd.Timestamp("2019-03-01")
