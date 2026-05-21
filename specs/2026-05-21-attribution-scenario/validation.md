# Phase 2 — Attribution & Scenario Analysis: Validation

## Definition of Done

Phase 2 is complete and ready to merge when all of the following pass.

## 1. Linter

```bash
ruff check .
```

Zero errors, zero warnings.

## 2. Test Suite

```bash
pytest tests/test_attribution.py tests/test_scenarios.py -v
```

All tests green. No skips.

## 3. Factor Attribution — Known-Output Fixtures

- `tests/test_attribution.py` feeds a synthetic 90-day `returns_df` + `factors_df` (committed as `tests/fixtures/factors.csv`) into `rolling_ols_attribution`.
- Rolling betas for the final window are compared against a hand-computed `statsmodels` OLS reference stored in `tests/fixtures/attribution_expected_betas.csv`.
- Tolerance: absolute difference ≤ 1e-6 for each beta coefficient.
- R² values are positive and ≤ 1.0 for all windows.

## 4. Contribution Decomposition — Known-Output Fixtures

- `contribution_decomposition` is run on a 5-row fixture `returns_df`.
- Daily contributions sum to the `total` column within `1e-10` absolute tolerance on every row.
- Cumulative contributions match `tests/fixtures/contribution_expected.csv`.

## 5. Historical Scenario Replay — Known-Output Fixtures

- `replay_scenario` is run on a fixture `returns_df` that spans a defined scenario date range (stored in `tests/fixtures/scenario_returns.csv`).
- Total P&L and per-subcomponent breakdown match `tests/fixtures/scenario_expected_pnl.csv` within `1e-8` tolerance.
- `replay_all` runs all default scenarios without raising exceptions.

## 6. Synthetic Scenario Engine — Behavioural Tests

- A zero-shock `run_scenario` (all `ShockParams` fields `None`) produces the same total P&L as the unshocked portfolio within `1e-10`.
- A positive `vol_shock` increases the magnitude of returns (P&L variance increases).
- A `spot_shock > 0` shifts returns in the expected direction relative to a known directional fixture.
- `ScenarioResult.pnl_by_component` values sum to `ScenarioResult.pnl_total` within `1e-10`.

## 7. Data Loader

- `load_factors` raises `FileNotFoundError` with a descriptive message when the path does not exist.
- `load_factors` raises `ValueError` if any of the four required columns (`carry`, `momentum`, `value`, `volatility`) are missing.
- Returns a `pd.DataFrame` with a `pd.DatetimeIndex`.

## Merge Gate

All items above must be checked before opening a PR to `main`. The PR description must link to this file.
