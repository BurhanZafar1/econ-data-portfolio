import pandas as pd
import pytest

from overcharge.data import DATA_FILE, N_WEEKS, load_jec, season_dummies, validate


@pytest.fixture(scope="module")
def df():
    return load_jec()


def test_shape_and_counts(df):
    assert len(df) == N_WEEKS
    assert df["cartel"].sum() == 203
    assert df["season"].between(1, 13).all()


def test_lakes_is_complement_of_ice(df):
    raw = pd.read_csv(DATA_FILE)
    assert ((raw["ice"] == "yes").astype(int) + df["lakes"] == 1).all()


def test_revenue_units(df):
    """$0.40 per 100 lbs on 1 ton (20 hundredweight) is $8."""
    row = df.iloc[0]
    assert row["revenue"] == pytest.approx(row["price"] * row["quantity"] * 20)


def test_season_dummies_keep_all_columns_in_a_subsample(df):
    sub = df[df["season"] == 1]
    assert list(season_dummies(sub).columns) == [f"seas_{i}" for i in range(1, 13)]


def test_validate_rejects_short_file(df):
    with pytest.raises(ValueError):
        validate(df.iloc[:-1])
