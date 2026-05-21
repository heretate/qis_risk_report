"""Unit tests for Phase 2 attribution and contribution decomposition.

Fixture: factors_90d.csv — 100 business days of carry/momentum/value/volatility
Fixture: returns_attribution_90d.csv — subcomponent returns are exact linear
    combinations of factors (no noise):
      sub1 = 0.30*carry + 0.20*momentum + 0.10*value + 0.15*volatility
      sub2 = 0.50*carry - 0.10*momentum + 0.20*value + 0.00*volatility
      sub3 = 0.00*carry + 0.40*momentum + 0.10*value + 0.20*volatility
      sub4 = 0.20*carry + 0.10*momentum + 0.30*value + 0.10*volatility
      total = (sub1 + sub2 + sub3 + sub4) / 4

Fixture: returns_contrib_10d.csv — sub1..sub4 chosen so that
    (sub1 + sub2 + sub3 + sub4) / 4 == total (verified to floating-point)
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from qis_risk_report.risk.attribution import (
    attribute_all,
    contribution_decomposition,
    cumulative_contribution,
    rolling_ols_attribution,
)

FIXTURES = Path(__file__).parent / "fixtures"
WINDOW = 60

# True betas embedded in the fixture
TRUE_BETAS = {
    "sub1": {"carry": 0.30, "momentum": 0.20, "value": 0.10, "volatility": 0.15},
    "sub2": {"carry": 0.50, "momentum": -0.10, "value": 0.20, "volatility": 0.00},
    "sub3": {"carry": 0.00, "momentum": 0.40, "value": 0.10, "volatility": 0.20},
    "sub4": {"carry": 0.20, "momentum": 0.10, "value": 0.30, "volatility": 0.10},
}


@pytest.fixture
def factors() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "factors_90d.csv", index_col="date", parse_dates=True)


@pytest.fixture
def returns_attr() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "returns_attribution_90d.csv", index_col="date", parse_dates=True)


@pytest.fixture
def returns_contrib() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "returns_contrib_10d.csv", index_col="date", parse_dates=True)


# ---------------------------------------------------------------------------
# Task Group 1 — Factor Attribution
# ---------------------------------------------------------------------------

def test_rolling_ols_output_shape(returns_attr, factors):
    result = rolling_ols_attribution(returns_attr["sub1"], factors, window=WINDOW)
    assert result.shape == (len(returns_attr), 5)  # 4 factors + r_squared


def test_rolling_ols_columns(returns_attr, factors):
    result = rolling_ols_attribution(returns_attr["sub1"], factors, window=WINDOW)
    assert list(result.columns) == ["carry", "momentum", "value", "volatility", "r_squared"]


def test_rolling_ols_nan_before_window(returns_attr, factors):
    result = rolling_ols_attribution(returns_attr["sub1"], factors, window=WINDOW)
    assert result.iloc[: WINDOW - 1].isna().all().all()


def test_rolling_ols_betas_match_statsmodels_reference(returns_attr, factors):
    """At the last row, rolling betas should match a direct statsmodels OLS on the same window."""
    col = "sub1"
    result = rolling_ols_attribution(returns_attr[col], factors, window=WINDOW)

    # statsmodels OLS on final window
    y = returns_attr[col].iloc[-WINDOW:]
    X = sm.add_constant(factors.iloc[-WINDOW:])
    ols = sm.OLS(y, X).fit()

    for factor in factors.columns:
        assert result[factor].iloc[-1] == pytest.approx(ols.params[factor], rel=1e-6)
    assert result["r_squared"].iloc[-1] == pytest.approx(ols.rsquared, rel=1e-6)


def test_rolling_ols_exact_betas_no_noise(returns_attr, factors):
    """With zero-noise fixture, final-window betas must recover true coefficients."""
    for col, expected in TRUE_BETAS.items():
        result = rolling_ols_attribution(returns_attr[col], factors, window=WINDOW)
        last_valid = result.dropna()
        for factor, true_beta in expected.items():
            assert last_valid[factor].iloc[-1] == pytest.approx(true_beta, abs=1e-5), \
                f"{col} {factor}: got {last_valid[factor].iloc[-1]:.6f}, expected {true_beta}"


def test_rolling_ols_r_squared_near_one_no_noise(returns_attr, factors):
    """With exact linear relationships, R² should be 1 (or extremely close)."""
    for col in TRUE_BETAS:
        result = rolling_ols_attribution(returns_attr[col], factors, window=WINDOW)
        last_valid = result.dropna()
        assert last_valid["r_squared"].iloc[-1] == pytest.approx(1.0, abs=1e-6), \
            f"{col} R²={last_valid['r_squared'].iloc[-1]:.8f}"


def test_attribute_all_keys(returns_attr, factors):
    results = attribute_all(returns_attr, factors, window=WINDOW)
    assert set(results.keys()) == set(returns_attr.columns)


def test_attribute_all_values_are_dataframes(returns_attr, factors):
    results = attribute_all(returns_attr, factors, window=WINDOW)
    for col, df in results.items():
        assert isinstance(df, pd.DataFrame), f"{col} is not a DataFrame"


# ---------------------------------------------------------------------------
# Task Group 2 — Contribution Decomposition
# ---------------------------------------------------------------------------

def test_contribution_decomposition_shape(returns_contrib):
    result = contribution_decomposition(returns_contrib)
    assert result.shape == (len(returns_contrib), 5)  # sub1..sub4 + total


def test_contribution_columns(returns_contrib):
    result = contribution_decomposition(returns_contrib)
    assert set(result.columns) == {"sub1", "sub2", "sub3", "sub4", "total"}


def test_contributions_sum_to_total_equal_weights(returns_contrib):
    """Sub-component contributions (×1/4 each) must sum to total within float tolerance."""
    result = contribution_decomposition(returns_contrib)
    sub_cols = ["sub1", "sub2", "sub3", "sub4"]
    computed_total = result[sub_cols].sum(axis=1)
    pd.testing.assert_series_equal(computed_total, result["total"], check_names=False, rtol=1e-9)


def test_contributions_match_original_total(returns_contrib):
    """The 'total' contribution column should equal the original total return series."""
    result = contribution_decomposition(returns_contrib)
    pd.testing.assert_series_equal(
        result["total"], returns_contrib["total"], check_names=False, rtol=1e-9
    )


def test_contribution_with_custom_weights(returns_contrib):
    """Custom weights must be honoured — contributions × weights sum to total."""
    sub_cols = ["sub1", "sub2", "sub3", "sub4"]
    w = pd.Series([0.5, 0.3, 0.1, 0.1], index=sub_cols)
    result = contribution_decomposition(returns_contrib, weights=w)
    computed_total = result[sub_cols].sum(axis=1)
    pd.testing.assert_series_equal(computed_total, result["total"], check_names=False, rtol=1e-9)


def test_contribution_individual_values(returns_contrib):
    """Each sub-contribution = sub_return × (1/4)."""
    result = contribution_decomposition(returns_contrib)
    for col in ["sub1", "sub2", "sub3", "sub4"]:
        expected = returns_contrib[col] * 0.25
        pd.testing.assert_series_equal(result[col], expected, check_names=False, rtol=1e-9)


def test_cumulative_contribution_last_row(returns_contrib):
    """Cumulative total contribution must equal sum of all daily totals."""
    cum = cumulative_contribution(returns_contrib)
    daily = contribution_decomposition(returns_contrib)
    assert cum["total"].iloc[-1] == pytest.approx(daily["total"].sum(), rel=1e-9)


def test_cumulative_contribution_monotone_if_positive():
    """Cumulative series is non-decreasing when all daily returns are positive."""
    idx = pd.bdate_range("2024-01-02", periods=5)
    df = pd.DataFrame(
        {"sub1": [0.01] * 5, "sub2": [0.01] * 5, "sub3": [0.01] * 5, "sub4": [0.01] * 5, "total": [0.01] * 5},
        index=idx,
    )
    cum = cumulative_contribution(df)
    assert (cum["total"].diff().dropna() >= 0).all()
