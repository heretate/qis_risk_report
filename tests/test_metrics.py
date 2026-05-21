"""Unit tests for Phase 1 core risk metrics.

Fixture: returns_5d_simple.csv — total column returns: [0.02, -0.01, 0.03, -0.02, 0.01]
Fixture: returns_20d.csv — total column: 5×0.01, 7×-0.02, 5×0.005, 3×0.05

Key hand-calculated values for `total` series in 5-day fixture:
  wealth:      [1.02, 1.0098, 1.040094, 1.0192921, 1.0294850]
  running_max: [1.02, 1.02,   1.040094, 1.040094,  1.040094 ]
  drawdown:    [0.0, -0.01,   0.0,      -0.02,      -0.0102  ]
  max_drawdown = -0.02 (exact: wealth[3]/running_max[3] - 1 = 0.98 - 1)
  drawdown_duration = 4 cal days (peak Jan-04, last below-peak Jan-08)

For 20-day fixture: drawdown_duration = 18 cal days (peak Jan-08, last below-peak Jan-26)
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from qis_risk_report.risk.metrics import (
    annualised_return,
    annualised_volatility,
    correlation_matrix,
    cumulative_return,
    drawdown_duration,
    drawdown_series,
    expected_shortfall,
    historical_var,
    max_drawdown,
    parametric_var,
    sharpe_ratio,
    sortino_ratio,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def returns_5d() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "returns_5d_simple.csv", index_col="date", parse_dates=True)


@pytest.fixture
def returns_20d() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "returns_20d.csv", index_col="date", parse_dates=True)


# ---------------------------------------------------------------------------
# 1. Return series
# ---------------------------------------------------------------------------

def test_cumulative_return(returns_5d):
    r = returns_5d["total"]
    result = cumulative_return(r)
    expected = (1 + r).cumprod() - 1
    assert isinstance(result, pd.Series)
    assert len(result) == 5
    pd.testing.assert_series_equal(result, expected)


def test_annualised_return(returns_5d):
    r = returns_5d["total"]
    result = annualised_return(r)
    expected = float((1 + r).prod() ** (252 / len(r)) - 1)
    assert result == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# 2. Volatility
# ---------------------------------------------------------------------------

def test_annualised_volatility_full_period(returns_5d):
    r = returns_5d["total"]
    result = annualised_volatility(r)
    expected = float(r.std() * np.sqrt(252))
    assert isinstance(result, float)
    assert result == pytest.approx(expected, rel=1e-9)


def test_annualised_volatility_rolling_window21_all_nan(returns_20d):
    # 20 rows < window=21: every value is NaN — tests correct NaN propagation
    r = returns_20d["total"]
    result = annualised_volatility(r, window=21)
    assert isinstance(result, pd.Series)
    assert len(result) == 20
    assert result.isna().all()


# ---------------------------------------------------------------------------
# 3. Risk-adjusted ratios
# ---------------------------------------------------------------------------

def test_sharpe_ratio_zero_risk_free(returns_5d):
    r = returns_5d["total"]
    result = sharpe_ratio(r)
    expected = annualised_return(r) / annualised_volatility(r)
    assert result == pytest.approx(expected, rel=1e-9)


def test_sharpe_ratio_nonzero_risk_free(returns_5d):
    r = returns_5d["total"]
    rf = 0.03
    result = sharpe_ratio(r, risk_free=rf)
    expected = (annualised_return(r) - rf) / annualised_volatility(r)
    assert result == pytest.approx(expected, rel=1e-9)


def test_sortino_ratio(returns_5d):
    r = returns_5d["total"]
    # downside returns: [-0.01, -0.02]
    downside = r[r < 0.0]
    expected_downside_vol = float(downside.std() * np.sqrt(252))
    expected = (annualised_return(r) - 0.0) / expected_downside_vol
    assert sortino_ratio(r) == pytest.approx(expected, rel=1e-9)


def test_sortino_ratio_larger_than_sharpe(returns_5d):
    # downside vol < total vol → sortino > sharpe for this fixture
    r = returns_5d["total"]
    assert sortino_ratio(r) > sharpe_ratio(r)


# ---------------------------------------------------------------------------
# 4. Drawdown
# ---------------------------------------------------------------------------

def test_drawdown_series_values(returns_5d):
    r = returns_5d["total"]
    result = drawdown_series(r)
    # See module docstring for derivation
    expected = pd.Series(
        [0.0, -0.01, 0.0, -0.02, -0.0102],
        index=r.index,
        name=r.name,
    )
    assert isinstance(result, pd.Series)
    assert len(result) == 5
    pd.testing.assert_series_equal(result, expected, check_exact=False, rtol=1e-9)


def test_drawdown_series_non_positive(returns_5d):
    r = returns_5d["total"]
    assert (drawdown_series(r) <= 0).all()


def test_max_drawdown(returns_5d):
    r = returns_5d["total"]
    # wealth[3]/running_max[3] - 1 = (1.040094 × 0.98)/1.040094 - 1 = 0.98 - 1 = -0.02
    assert max_drawdown(r) == pytest.approx(-0.02, rel=1e-9)


def test_drawdown_duration_5d(returns_5d):
    r = returns_5d["total"]
    # Period 1: peak Jan-02, last below-peak Jan-03 → 1 cal day
    # Period 2: peak Jan-04, last below-peak Jan-08 → 4 cal days
    assert drawdown_duration(r) == 4


def test_drawdown_duration_20d(returns_20d):
    r = returns_20d["total"]
    # Peak Jan-08, last below-peak Jan-26 → 18 cal days
    assert drawdown_duration(r) == 18


def test_drawdown_duration_no_drawdown():
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    r = pd.Series([0.01, 0.02, 0.03, 0.01, 0.02], index=idx)
    assert drawdown_duration(r) == 0


# ---------------------------------------------------------------------------
# 5. Historical VaR
# ---------------------------------------------------------------------------

def test_historical_var_99_1d(returns_5d):
    r = returns_5d["total"]
    # quantile(0.01) on 5 values sorted [-0.02, -0.01, 0.01, 0.02, 0.03]:
    # virtual_idx = 0.01×4 = 0.04 → -0.02 + 0.04×0.01 = -0.0196 → VaR = 0.0196
    assert historical_var(r, confidence=0.99, horizon=1) == pytest.approx(0.0196, rel=1e-9)


def test_historical_var_99_10d(returns_5d):
    r = returns_5d["total"]
    expected = 0.0196 * np.sqrt(10)
    assert historical_var(r, confidence=0.99, horizon=10) == pytest.approx(expected, rel=1e-9)


def test_historical_var_95_1d(returns_5d):
    r = returns_5d["total"]
    # quantile(0.05): virtual_idx = 0.05×4 = 0.2 → -0.02 + 0.2×0.01 = -0.018 → VaR = 0.018
    assert historical_var(r, confidence=0.95, horizon=1) == pytest.approx(0.018, rel=1e-9)


def test_historical_var_95_10d(returns_5d):
    r = returns_5d["total"]
    expected = 0.018 * np.sqrt(10)
    assert historical_var(r, confidence=0.95, horizon=10) == pytest.approx(expected, rel=1e-9)


def test_historical_var_positive(returns_5d):
    r = returns_5d["total"]
    assert historical_var(r) > 0


# ---------------------------------------------------------------------------
# 6. Parametric VaR
# ---------------------------------------------------------------------------

def test_parametric_var_99_1d(returns_5d):
    r = returns_5d["total"]
    mu, sigma = r.mean(), r.std()
    z = norm.ppf(0.01)
    expected = -(mu + z * sigma)
    assert parametric_var(r, confidence=0.99, horizon=1) == pytest.approx(expected, rel=1e-9)


def test_parametric_var_99_10d(returns_5d):
    r = returns_5d["total"]
    mu, sigma = r.mean(), r.std()
    z = norm.ppf(0.01)
    expected = -(mu + z * sigma) * np.sqrt(10)
    assert parametric_var(r, confidence=0.99, horizon=10) == pytest.approx(expected, rel=1e-9)


def test_parametric_var_95_1d(returns_5d):
    r = returns_5d["total"]
    mu, sigma = r.mean(), r.std()
    z = norm.ppf(0.05)
    expected = -(mu + z * sigma)
    assert parametric_var(r, confidence=0.95, horizon=1) == pytest.approx(expected, rel=1e-9)


def test_parametric_var_95_10d(returns_5d):
    r = returns_5d["total"]
    mu, sigma = r.mean(), r.std()
    z = norm.ppf(0.05)
    expected = -(mu + z * sigma) * np.sqrt(10)
    assert parametric_var(r, confidence=0.95, horizon=10) == pytest.approx(expected, rel=1e-9)


def test_parametric_var_positive(returns_5d):
    r = returns_5d["total"]
    assert parametric_var(r) > 0


# ---------------------------------------------------------------------------
# 7. Expected Shortfall
# ---------------------------------------------------------------------------

def test_expected_shortfall_99(returns_5d):
    r = returns_5d["total"]
    # threshold = -0.0196; only -0.02 is at or below → ES = 0.02
    assert expected_shortfall(r, confidence=0.99) == pytest.approx(0.02, rel=1e-9)


def test_expected_shortfall_95(returns_5d):
    r = returns_5d["total"]
    # threshold = -0.018; only -0.02 is at or below → ES = 0.02
    assert expected_shortfall(r, confidence=0.95) == pytest.approx(0.02, rel=1e-9)


def test_expected_shortfall_positive(returns_5d):
    r = returns_5d["total"]
    assert expected_shortfall(r) > 0


def test_expected_shortfall_gte_historical_var(returns_5d):
    # ES ≥ VaR by definition
    r = returns_5d["total"]
    assert expected_shortfall(r) >= historical_var(r)


# ---------------------------------------------------------------------------
# 8. Correlation matrix
# ---------------------------------------------------------------------------

def test_correlation_matrix_shape(returns_5d):
    result = correlation_matrix(returns_5d)
    assert result.shape == (5, 5)


def test_correlation_matrix_diagonal(returns_5d):
    result = correlation_matrix(returns_5d)
    np.testing.assert_allclose(np.diag(result.values), 1.0)


def test_correlation_matrix_symmetric(returns_5d):
    result = correlation_matrix(returns_5d)
    pd.testing.assert_frame_equal(result, result.T)
