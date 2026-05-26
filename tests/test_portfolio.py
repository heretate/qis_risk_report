"""Unit tests for Phase 3 portfolio risk contribution.

Fixtures:
  portfolio_returns.csv — 60 business days, 5 instruments + qis_total, seed=42
  weights.csv           — static allocation: inst1=0.20, inst2=0.20, inst3=0.15,
                          inst4=0.15, inst5=0.10, qis_total=0.20
  marginal_var_expected.csv / component_var_expected.csv — pre-computed from above
  portfolio_correlation_expected.csv — Pearson correlations vs equal-weight aggregate
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from qis_risk_report.data.loaders import load_portfolio, load_weights
from qis_risk_report.risk.portfolio import (
    build_portfolio_contribution_grid,
    component_var,
    diversification_benefit,
    marginal_var,
    portfolio_var,
    qis_portfolio_correlation,
)

FIXTURES = Path(__file__).parent / "fixtures"
CONFIDENCE = 0.95


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def port_ret() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "portfolio_returns.csv", index_col="date", parse_dates=True)


@pytest.fixture
def weights(port_ret) -> pd.Series:
    df = pd.read_csv(FIXTURES / "weights.csv", index_col="date", parse_dates=True)
    return df.iloc[-1]


# ---------------------------------------------------------------------------
# Task Group 1 — Data Loaders
# ---------------------------------------------------------------------------


def test_load_portfolio_happy_path():
    df = load_portfolio(str(FIXTURES / "portfolio_returns.csv"))
    assert isinstance(df, pd.DataFrame)
    assert isinstance(df.index, pd.DatetimeIndex)
    assert "qis_total" in df.columns


def test_load_portfolio_missing_file():
    with pytest.raises(FileNotFoundError, match="portfolio_returns"):
        load_portfolio("nonexistent_portfolio.csv")


def test_load_portfolio_missing_qis_total(tmp_path):
    p = tmp_path / "bad.csv"
    idx = pd.bdate_range("2024-01-02", periods=5)
    pd.DataFrame({"inst1": [0.01] * 5}, index=idx).to_csv(p, index_label="date")
    with pytest.raises(ValueError, match="qis_total"):
        load_portfolio(str(p))


def test_load_weights_happy_path():
    df = load_weights(str(FIXTURES / "weights.csv"))
    assert isinstance(df, pd.DataFrame)
    assert isinstance(df.index, pd.DatetimeIndex)
    assert "qis_total" in df.columns


def test_load_weights_missing_file():
    with pytest.raises(FileNotFoundError, match="weights"):
        load_weights("nonexistent_weights.csv")


def test_load_weights_missing_qis_total(tmp_path):
    p = tmp_path / "bad_weights.csv"
    idx = pd.DatetimeIndex(["2024-01-02"], name="date")
    pd.DataFrame({"inst1": [0.5], "inst2": [0.5]}, index=idx).to_csv(p)
    with pytest.raises(ValueError, match="qis_total"):
        load_weights(str(p))


def test_load_weights_rows_not_summing_to_one(tmp_path):
    p = tmp_path / "bad_sums.csv"
    idx = pd.DatetimeIndex(["2024-01-02"], name="date")
    pd.DataFrame({"inst1": [0.5], "inst2": [0.4], "qis_total": [0.2]}, index=idx).to_csv(p)
    with pytest.raises(ValueError, match="sum"):
        load_weights(str(p))


# ---------------------------------------------------------------------------
# Task Group 2 — Marginal VaR
# ---------------------------------------------------------------------------


def test_marginal_var_values_match_fixture(port_ret, weights):
    expected = pd.read_csv(
        FIXTURES / "marginal_var_expected.csv", index_col=0
    )["marginal_var"]
    result = marginal_var(port_ret, weights, confidence=CONFIDENCE)
    for instr in expected.index:
        assert result[instr] == pytest.approx(expected[instr], abs=1e-6), (
            f"marginal_var[{instr}]: got {result[instr]:.8f}, expected {expected[instr]:.8f}"
        )


def test_marginal_var_sums_to_portfolio_var(port_ret, weights):
    result = marginal_var(port_ret, weights, confidence=CONFIDENCE)
    pvar = portfolio_var(port_ret, weights, confidence=CONFIDENCE)
    assert result.sum() == pytest.approx(pvar, abs=1e-8)


# ---------------------------------------------------------------------------
# Task Group 2 — Component VaR
# ---------------------------------------------------------------------------


def test_component_var_values_match_fixture(port_ret, weights):
    expected = pd.read_csv(
        FIXTURES / "component_var_expected.csv", index_col=0
    )["component_var"]
    result = component_var(port_ret, weights, confidence=CONFIDENCE)
    for instr in expected.index:
        assert result[instr] == pytest.approx(expected[instr], abs=1e-6), (
            f"component_var[{instr}]: got {result[instr]:.8f}, expected {expected[instr]:.8f}"
        )


def test_component_var_sums_to_portfolio_var(port_ret, weights):
    result = component_var(port_ret, weights, confidence=CONFIDENCE)
    pvar = portfolio_var(port_ret, weights, confidence=CONFIDENCE)
    assert result.sum() == pytest.approx(pvar, abs=1e-8)


# ---------------------------------------------------------------------------
# Task Group 3 — QIS-Portfolio Correlation
# ---------------------------------------------------------------------------


def test_qis_portfolio_correlation_values_match_fixture(port_ret):
    expected = pd.read_csv(
        FIXTURES / "portfolio_correlation_expected.csv", index_col=0
    )["correlation"]
    result = qis_portfolio_correlation(port_ret, port_ret)
    for instr in expected.index:
        assert result[instr] == pytest.approx(expected[instr], abs=1e-6), (
            f"correlation[{instr}]: got {result[instr]:.8f}, expected {expected[instr]:.8f}"
        )


def test_qis_portfolio_correlation_range(port_ret):
    result = qis_portfolio_correlation(port_ret, port_ret)
    assert (result >= -1.0).all() and (result <= 1.0).all()


# ---------------------------------------------------------------------------
# Task Group 3 — Diversification Benefit
# ---------------------------------------------------------------------------


def test_diversification_benefit_non_negative(port_ret, weights):
    benefit = diversification_benefit(port_ret, weights, confidence=CONFIDENCE)
    assert benefit >= 0.0


def test_diversification_benefit_formula(port_ret, weights):
    from scipy.stats import norm
    w = weights.reindex(port_ret.columns)
    z = norm.ppf(CONFIDENCE)
    standalone_sum = float((w * z * port_ret.std()).sum())
    pvar = portfolio_var(port_ret, weights, confidence=CONFIDENCE)
    expected = standalone_sum - pvar
    result = diversification_benefit(port_ret, weights, confidence=CONFIDENCE)
    assert result == pytest.approx(expected, abs=1e-8)


def test_diversification_benefit_perfectly_correlated_near_zero():
    """Perfectly correlated instruments produce ~zero diversification benefit."""
    idx = pd.bdate_range("2024-01-02", periods=60)
    vals = [i * 0.001 - 0.03 for i in range(60)]
    df = pd.DataFrame(
        {"a": vals, "b": vals, "c": vals, "qis_total": vals},
        index=idx,
    )
    w = pd.Series([0.25, 0.25, 0.25, 0.25], index=["a", "b", "c", "qis_total"])
    benefit = diversification_benefit(df, w, confidence=CONFIDENCE)
    assert abs(benefit) < 1e-8


def test_diversification_benefit_raises_on_degenerate_inputs(monkeypatch):
    """Defensive check: if portfolio_var somehow exceeds standalone sum, raise ValueError.

    A negative benefit is mathematically impossible with a valid covariance matrix
    (Cauchy-Schwarz guarantees non-negativity), but the guard exists for floating-point
    edge cases or mismatched data. We test it via monkeypatching portfolio_var.
    """
    import qis_risk_report.risk.portfolio as mod

    monkeypatch.setattr(mod, "portfolio_var", lambda *a, **kw: 999.0)
    idx = pd.bdate_range("2024-01-02", periods=10)
    df = pd.DataFrame({"a": [0.01] * 10, "qis_total": [0.01] * 10}, index=idx)
    w = pd.Series([0.5, 0.5], index=["a", "qis_total"])
    with pytest.raises(ValueError):
        diversification_benefit(df, w, confidence=CONFIDENCE)


# ---------------------------------------------------------------------------
# Task Group 4 — Allocation Sensitivity Grid
# ---------------------------------------------------------------------------


@pytest.fixture
def sensitivity_fixtures():
    """Synthetic 60-day QIS + portfolio DataFrames for sensitivity grid tests."""
    rng = np.random.default_rng(42)
    n = 60
    dates = pd.bdate_range("2022-01-03", periods=n)

    sub_ret = rng.normal(0.0003, 0.007, (n, 4))
    qis_df = pd.DataFrame(sub_ret, index=dates, columns=["sub1", "sub2", "sub3", "sub4"])
    qis_df.index.name = "date"
    qis_df["total"] = qis_df.mean(axis=1)

    port_ret = rng.normal(0.0002, 0.010, (n, 5))
    port_cols = ["inst1", "inst2", "inst3", "inst4", "inst5"]
    port_df = pd.DataFrame(port_ret, index=dates, columns=port_cols)
    port_df.index.name = "date"
    port_df["qis_total"] = qis_df["total"].values

    weights_data = {
        "inst1": 0.20, "inst2": 0.20, "inst3": 0.15,
        "inst4": 0.15, "inst5": 0.10, "qis_total": 0.20,
    }
    w_df = pd.DataFrame([weights_data], index=[dates[-1]])
    w_df.index.name = "date"

    return qis_df, port_df, w_df


def test_grid_shape(sensitivity_fixtures):
    qis_df, port_df, w_df = sensitivity_fixtures
    weights_list = [0.01, 0.05]
    grid = build_portfolio_contribution_grid(qis_df, port_df, w_df, weights_list)
    assert grid.shape == (2, 5)


def test_grid_index_labels(sensitivity_fixtures):
    qis_df, port_df, w_df = sensitivity_fixtures
    weights_list = [0.01, 0.05]
    grid = build_portfolio_contribution_grid(qis_df, port_df, w_df, weights_list)
    assert list(grid.index) == ["1.0%", "5.0%"]


def test_grid_columns(sensitivity_fixtures):
    qis_df, port_df, w_df = sensitivity_fixtures
    grid = build_portfolio_contribution_grid(qis_df, port_df, w_df, [0.01])
    expected_cols = {
        "standalone_var", "marginal_var", "component_var_share",
        "correlation", "diversification_benefit",
    }
    assert set(grid.columns) == expected_cols


def test_grid_values_finite(sensitivity_fixtures):
    qis_df, port_df, w_df = sensitivity_fixtures
    grid = build_portfolio_contribution_grid(qis_df, port_df, w_df, [0.01, 0.025, 0.05, 0.10])
    assert np.isfinite(grid.values).all(), f"Non-finite values found:\n{grid}"


def test_grid_standalone_var_positive(sensitivity_fixtures):
    qis_df, port_df, w_df = sensitivity_fixtures
    grid = build_portfolio_contribution_grid(qis_df, port_df, w_df, [0.01, 0.05])
    assert (grid["standalone_var"] > 0).all()


def test_grid_component_var_share_increases_with_weight(sensitivity_fixtures):
    """Higher QIS allocation should generally mean higher component VaR share."""
    qis_df, port_df, w_df = sensitivity_fixtures
    grid = build_portfolio_contribution_grid(qis_df, port_df, w_df, [0.01, 0.05, 0.10])
    assert grid["component_var_share"].iloc[-1] > grid["component_var_share"].iloc[0]
