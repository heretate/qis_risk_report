"""Unit tests for Phase 2 historical and synthetic scenario analysis.

Fixture: returns_scenario_30d.csv — 30 business days, 5 sub-components + total.
  total = (sub1 + sub2 + sub3 + sub4) / 4 (equal-weight definition).

Scenario under test: "2024-01-09" to "2024-01-15" (5 business days):
  sub1 = -0.020 each → pnl = -0.10
  sub2 = +0.015 each → pnl = +0.075
  sub3 = -0.005 each → pnl = -0.025
  sub4 = +0.001 each → pnl = +0.005
  total per day = (-0.020 + 0.015 - 0.005 + 0.001) / 4 = -0.00225
  pnl_total = -0.01125
"""
from pathlib import Path

import pandas as pd
import pytest

from qis_risk_report.risk.scenarios import (
    HistoricalScenario,
    ScenarioResult,
    ShockParams,
    default_scenarios,
    replay_all,
    replay_scenario,
    run_scenario,
)

FIXTURES = Path(__file__).parent / "fixtures"

SCENARIO_NAME  = "Test Scenario"
SCENARIO_START = "2024-01-09"
SCENARIO_END   = "2024-01-15"

EXPECTED_PNL_TOTAL  = pytest.approx(-0.01125, abs=1e-9)
EXPECTED_PNL_SUB1   = pytest.approx(-0.10, abs=1e-9)
EXPECTED_PNL_SUB2   = pytest.approx( 0.075, abs=1e-9)
EXPECTED_PNL_SUB3   = pytest.approx(-0.025, abs=1e-9)
EXPECTED_PNL_SUB4   = pytest.approx( 0.005, abs=1e-9)


@pytest.fixture
def returns_30d() -> pd.DataFrame:
    return pd.read_csv(FIXTURES / "returns_scenario_30d.csv", index_col="date", parse_dates=True)


@pytest.fixture
def test_scenario() -> HistoricalScenario:
    return HistoricalScenario(SCENARIO_NAME, SCENARIO_START, SCENARIO_END)


# ---------------------------------------------------------------------------
# Task Group 3 — Historical Scenario Replay
# ---------------------------------------------------------------------------

def test_replay_scenario_returns_result(returns_30d, test_scenario):
    result = replay_scenario(test_scenario, returns_30d)
    assert isinstance(result, ScenarioResult)


def test_replay_scenario_name(returns_30d, test_scenario):
    result = replay_scenario(test_scenario, returns_30d)
    assert result.name == SCENARIO_NAME


def test_replay_scenario_pnl_total(returns_30d, test_scenario):
    result = replay_scenario(test_scenario, returns_30d)
    assert result.pnl_total == EXPECTED_PNL_TOTAL


def test_replay_scenario_pnl_by_component(returns_30d, test_scenario):
    result = replay_scenario(test_scenario, returns_30d)
    assert result.pnl_by_component["sub1"] == EXPECTED_PNL_SUB1
    assert result.pnl_by_component["sub2"] == EXPECTED_PNL_SUB2
    assert result.pnl_by_component["sub3"] == EXPECTED_PNL_SUB3
    assert result.pnl_by_component["sub4"] == EXPECTED_PNL_SUB4


def test_replay_scenario_metadata_n_days(returns_30d, test_scenario):
    result = replay_scenario(test_scenario, returns_30d)
    assert result.metadata["n_days"] == 5


def test_replay_scenario_empty_range_returns_zero(returns_30d):
    out_of_range = HistoricalScenario("empty", "2030-01-01", "2030-01-31")
    result = replay_scenario(out_of_range, returns_30d)
    assert result.pnl_total == pytest.approx(0.0, abs=1e-12)


def test_replay_all_length(returns_30d):
    scenarios = [
        HistoricalScenario("s1", "2024-01-02", "2024-01-08"),
        HistoricalScenario("s2", "2024-01-09", "2024-01-15"),
    ]
    results = replay_all(scenarios, returns_30d)
    assert len(results) == 2


def test_replay_all_names(returns_30d):
    scenarios = [
        HistoricalScenario("alpha", "2024-01-02", "2024-01-08"),
        HistoricalScenario("beta",  "2024-01-09", "2024-01-15"),
    ]
    results = replay_all(scenarios, returns_30d)
    assert [r.name for r in results] == ["alpha", "beta"]


def test_default_scenarios_returns_list():
    scenarios = default_scenarios()
    assert isinstance(scenarios, list)
    assert all(isinstance(s, HistoricalScenario) for s in scenarios)
    assert len(scenarios) >= 1


# ---------------------------------------------------------------------------
# Task Group 4 — Synthetic Scenario Engine
# ---------------------------------------------------------------------------

def _portfolio_window(returns_30d: pd.DataFrame) -> pd.DataFrame:
    """Sub-component returns for the scenario window (no 'total' column)."""
    sub_cols = [c for c in returns_30d.columns if c != "total"]
    return returns_30d.loc[SCENARIO_START:SCENARIO_END, sub_cols].copy()


def test_run_scenario_zero_shock_matches_replay(returns_30d, test_scenario):
    """Zero-shock run must reproduce the same pnl_total as replay_scenario."""
    baseline = replay_scenario(test_scenario, returns_30d)
    portfolio = _portfolio_window(returns_30d)
    shocked = run_scenario(portfolio, ShockParams())
    assert shocked.pnl_total == pytest.approx(baseline.pnl_total, rel=1e-9)


def test_run_scenario_returns_scenario_result(returns_30d):
    portfolio = _portfolio_window(returns_30d)
    result = run_scenario(portfolio, ShockParams())
    assert isinstance(result, ScenarioResult)


def test_run_scenario_pnl_by_component_keys(returns_30d):
    portfolio = _portfolio_window(returns_30d)
    result = run_scenario(portfolio, ShockParams())
    assert set(result.pnl_by_component.keys()) == {"sub1", "sub2", "sub3", "sub4"}


def test_spot_shock_positive_increases_pnl(returns_30d):
    """Positive spot_shock (uniform additive) always increases total P&L."""
    portfolio = _portfolio_window(returns_30d)
    baseline = run_scenario(portfolio, ShockParams())
    shocked  = run_scenario(portfolio, ShockParams(spot_shock=0.01))
    assert shocked.pnl_total > baseline.pnl_total


def test_spot_shock_negative_decreases_pnl(returns_30d):
    portfolio = _portfolio_window(returns_30d)
    baseline = run_scenario(portfolio, ShockParams())
    shocked  = run_scenario(portfolio, ShockParams(spot_shock=-0.01))
    assert shocked.pnl_total < baseline.pnl_total


def test_spot_shock_pnl_delta(returns_30d):
    """P&L change from spot_shock must equal shock × n_days × n_cols / n_cols."""
    portfolio = _portfolio_window(returns_30d)
    shock = 0.005
    baseline = run_scenario(portfolio, ShockParams())
    shocked  = run_scenario(portfolio, ShockParams(spot_shock=shock))
    n_days = len(portfolio)
    assert shocked.pnl_total - baseline.pnl_total == pytest.approx(shock * n_days, rel=1e-9)


def test_vol_shock_positive_scales_up_positive_pnl():
    """vol_shock>0 multiplies returns by (1+shock), increasing P&L when P&L>0."""
    idx = pd.bdate_range("2024-01-02", periods=5)
    df = pd.DataFrame(
        {"sub1": [0.01] * 5, "sub2": [0.01] * 5, "sub3": [0.01] * 5, "sub4": [0.01] * 5},
        index=idx,
    )
    baseline = run_scenario(df, ShockParams())
    shocked  = run_scenario(df, ShockParams(vol_shock=0.2))
    assert shocked.pnl_total > baseline.pnl_total


def test_vol_shock_negative_scales_down_positive_pnl():
    idx = pd.bdate_range("2024-01-02", periods=5)
    df = pd.DataFrame(
        {"sub1": [0.01] * 5, "sub2": [0.01] * 5, "sub3": [0.01] * 5, "sub4": [0.01] * 5},
        index=idx,
    )
    baseline = run_scenario(df, ShockParams())
    shocked  = run_scenario(df, ShockParams(vol_shock=-0.5))
    assert shocked.pnl_total < baseline.pnl_total


def test_corr_shock_preserves_total_pnl(returns_30d):
    """corr_shock blends columns toward cross-mean; total P&L is preserved."""
    portfolio = _portfolio_window(returns_30d)
    baseline = run_scenario(portfolio, ShockParams())
    shocked  = run_scenario(portfolio, ShockParams(corr_shock=0.5))
    assert shocked.pnl_total == pytest.approx(baseline.pnl_total, rel=1e-9)


def test_corr_shock_full_equalises_components(returns_30d):
    """corr_shock=1.0 collapses all sub-component P&Ls to the cross-mean."""
    portfolio = _portfolio_window(returns_30d)
    shocked = run_scenario(portfolio, ShockParams(corr_shock=1.0))
    pnls = list(shocked.pnl_by_component.values())
    assert max(pnls) == pytest.approx(min(pnls), rel=1e-9)


def test_combined_shocks(returns_30d):
    """Applying spot + vol shocks together must not raise an error."""
    portfolio = _portfolio_window(returns_30d)
    result = run_scenario(portfolio, ShockParams(spot_shock=0.005, vol_shock=0.1, corr_shock=0.3))
    assert isinstance(result, ScenarioResult)
    assert isinstance(result.pnl_total, float)
