"""Known answer tests against published numbers on the same data.

Porter (1983), Table 2: summary statistics of the JEC series.
MIT 14.271 (Fall 2022) Problem Set 5 solutions, Table 1: OLS, first stage
and IV demand regressions on Porter's data with Stata robust (HC1) errors.
"""

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from overcharge.data import load_jec, season_dummies
from overcharge.models import demand_elasticity, fit_dummy


@pytest.fixture(scope="module")
def df():
    return load_jec()


def test_porter_table2_summary_statistics(df):
    assert df["price"].mean() == pytest.approx(0.2465, abs=5e-5)
    assert df["price"].std() == pytest.approx(0.06653, abs=5e-6)
    assert df["price"].min() == 0.125 and df["price"].max() == 0.40
    assert df["cartel"].mean() == pytest.approx(0.6189, abs=5e-5)


def test_ols_demand_matches_published_column_1(df):
    X = sm.add_constant(pd.concat([df[["log_price", "lakes"]].astype(float), season_dummies(df)], axis=1))
    fit = sm.OLS(df["log_quantity"], X).fit(cov_type="HC1")
    assert fit.params["log_price"] == pytest.approx(-0.639, abs=5e-4)
    assert fit.bse["log_price"] == pytest.approx(0.0733, abs=5e-5)
    assert fit.params["lakes"] == pytest.approx(-0.448, abs=5e-4)
    assert fit.params["const"] == pytest.approx(9.309, abs=5e-4)
    assert fit.rsquared == pytest.approx(0.313, abs=5e-4)


def test_first_stage_matches_published_column_4(df):
    """Log price on the cartel dummy and seasons: the 'seasons only' overcharge."""
    X = sm.add_constant(pd.concat([df[["cartel"]].astype(float), season_dummies(df)], axis=1))
    fit = sm.OLS(df["log_price"], X).fit(cov_type="HC1")
    assert fit.params["cartel"] == pytest.approx(0.356, abs=5e-4)
    assert fit.bse["cartel"] == pytest.approx(0.0261, abs=5e-5)
    assert fit.params["const"] == pytest.approx(-1.660, abs=5e-4)
    assert fit.rsquared == pytest.approx(0.488, abs=5e-4)
    # Same point estimate as the project's own dummy variable routine.
    assert fit_dummy(df, "check", seasons=True, lakes=False).b == pytest.approx(fit.params["cartel"])


def test_iv_demand_elasticity_matches_published_column_2(df):
    elasticity, se = demand_elasticity(df)
    assert elasticity == pytest.approx(-0.867, abs=5e-4)
    assert se == pytest.approx(0.134, abs=5e-4)


def test_no_control_dummy_equals_difference_in_mean_log_price(df):
    """Hand calculation: with only a dummy, OLS gives the difference in group means."""
    means = df.groupby("cartel")["log_price"].mean()
    assert fit_dummy(df, "raw", seasons=False, lakes=False).b == pytest.approx(means[1] - means[0])
    assert np.isclose(means[1] - means[0], 0.364178, atol=1e-6)
