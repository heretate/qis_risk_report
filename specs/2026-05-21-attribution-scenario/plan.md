# Phase 2 — Attribution & Scenario Analysis: Plan

## Task Group 1 — Factor Attribution

1. Add `factors_df` to the data contract: load from a separate CSV via a new `load_factors(path) -> pd.DataFrame` helper in `src/qis_risk_report/data/loaders.py`. Same `DatetimeIndex` as `returns_df`. Columns: `carry`, `momentum`, `value`, `volatility`.
2. Implement `rolling_ols_attribution(returns: pd.Series, factors: pd.DataFrame, window: int = 60) -> pd.DataFrame` in `src/qis_risk_report/risk/attribution.py`. Returns a DataFrame of rolling beta coefficients (one column per factor) and rolling R².
3. Apply to each of the 4 QIS subcomponents and `total`; expose `attribute_all(returns_df, factors_df, window) -> dict[str, pd.DataFrame]`.
4. Write unit tests in `tests/test_attribution.py` with CSV fixtures covering at least a 90-day synthetic series; verify betas match a hand-computed statsmodels OLS reference.

## Task Group 2 — Contribution-to-Return Decomposition

5. Implement `contribution_decomposition(returns_df: pd.DataFrame) -> pd.DataFrame` in `attribution.py`. For each date, each subcomponent's contribution = its return × its equal weight (1/4); `total` column is the sum. Accept an optional `weights` argument for non-equal allocation.
6. Compute cumulative contribution series alongside daily.
7. Write unit tests with known-input / known-output fixtures; verify contributions sum to `total` return within floating-point tolerance.

## Task Group 3 — Historical Scenario Replay

8. Implement `HistoricalScenario` dataclass in `src/qis_risk_report/risk/scenarios.py`: fields `name: str`, `start: str`, `end: str`. Provide a default registry function `default_scenarios() -> list[HistoricalScenario]` (configurable via `settings.yaml`).
9. Implement `replay_scenario(scenario: HistoricalScenario, returns_df: pd.DataFrame) -> ScenarioResult` — filters the date range, computes total P&L and per-subcomponent breakdown.
10. Expose `replay_all(scenarios, returns_df) -> list[ScenarioResult]`.
11. Write unit tests with a fixture `returns_df` spanning at least one defined scenario period; assert P&L matches expected values.

## Task Group 4 — Synthetic Scenario Engine

12. Define `ShockParams` dataclass: `spot_shock: float | None`, `vol_shock: float | None`, `corr_shock: float | None`. All optional; unspecified dimensions are left unchanged.
13. Implement `ScenarioResult` dataclass: `name: str`, `pnl_total: float`, `pnl_by_component: dict[str, float]`, `metadata: dict`.
14. Implement `run_scenario(portfolio: pd.DataFrame, shock_params: ShockParams) -> ScenarioResult` in `scenarios.py`. Applies shocks to `portfolio` returns and recomputes P&L.
15. Write unit tests: verify that a zero-shock run returns the same P&L as `replay_scenario`; verify each shock type shifts P&L in the expected direction.
