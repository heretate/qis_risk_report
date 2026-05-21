# Phase 2 — Attribution & Scenario Analysis: Requirements

## Scope

Implement factor attribution (rolling OLS), contribution-to-return decomposition, historical scenario replay, and a synthetic scenario engine within the `risk/` and `scenarios/` modules.

## Data Contract Additions

**`factors_df`** — FX risk factor daily returns (new input, Phase 2 only):

| Field | Type | Notes |
|---|---|---|
| Index | `pd.DatetimeIndex` | Business-day frequency, tz-naive, aligned to `returns_df` |
| `carry` | `float64` | Daily carry factor return |
| `momentum` | `float64` | Daily momentum factor return |
| `value` | `float64` | Daily value factor return |
| `volatility` | `float64` | Daily volatility factor return |

Loaded from a separate CSV (path in `config/settings.yaml`) via a new `load_factors(path) -> pd.DataFrame` helper. Do **not** add factor columns to `returns_df`.

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Factor attribution method | Rolling OLS via `statsmodels` | Already in the tech stack; supports rolling windows natively |
| OLS window | 60 calendar days (default, overridable) | Enough history for stable betas; short enough to be responsive |
| Historical stress periods | Configurable via `settings.yaml` (not hard-coded) | Allows PMs to add new events without code changes |
| Synthetic shock dimensions | Spot, vol, correlation shocks only | Keeps the API simple for MVP; Greeks / path simulation deferred |
| ScenarioResult API | `run_scenario(portfolio, shock_params) -> ScenarioResult` | Clean, testable contract defined by the roadmap |
| Contribution weights | Equal (1/4 per subcomponent) by default; optional `weights` arg | Matches current equal-weight QIS construction; extensible |

## Out of Scope for Phase 2

- Multi-asset Greeks or path simulation in synthetic scenarios
- Factor data sourcing / normalization (supplied as CSV by the external pipeline)
- Report rendering (Phase 4)
- Portfolio-level risk contribution (Phase 3)

## File Structure

```
src/qis_risk_report/
├── data/
│   └── loaders.py          # add load_factors()
└── risk/
    ├── attribution.py       # rolling_ols_attribution(), attribute_all(), contribution_decomposition()
    └── scenarios.py         # HistoricalScenario, ShockParams, ScenarioResult, run_scenario(), replay_scenario(), replay_all()
tests/
├── test_attribution.py
├── test_scenarios.py
└── fixtures/
    ├── factors.csv
    ├── attribution_expected_betas.csv
    ├── contribution_expected.csv
    ├── scenario_returns.csv
    └── scenario_expected_pnl.csv
config/
└── settings.yaml            # add factors_path, historical_scenarios list
```

## Context

Phase 1 (core risk metrics) is complete. Phase 2 explains *why* returns occur (attribution) and *what would happen* under stress (scenarios). Both modules feed the Phase 4 report notebook. The `scenarios/` module's clean API (`run_scenario`) is a hard contract — the notebook will call it directly.
