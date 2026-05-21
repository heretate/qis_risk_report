# Requirements — Phase 1: Core Risk Metrics

## Scope

Implement every metric listed in Phase 1 of the roadmap.  All logic lives in
`src/qis_risk_report/risk/metrics.py`; every public function must have a unit
test in `tests/`.  No new modules, no CLI wiring, no report rendering — those
belong to later phases.

## Input

`returns_df` as defined in the data contract:

| Field | Type | Notes |
|---|---|---|
| Index | `pd.DatetimeIndex` | Business-day frequency, tz-naive |
| `<subcomponent>` × 4 | `float64` | Simple daily return (e.g. `0.0012` = +0.12 %) |
| `total` | `float64` | Aggregate QIS strategy daily return |

The DataFrame is loaded by `data/loaders.py::load_returns` which is already
implemented and validated.  All metric functions accept a `pd.Series` (single
column) or `pd.DataFrame` (multi-column) as stated in the stub signatures.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Annualisation factor | 252 trading days | Already declared as `TRADING_DAYS` constant in stub |
| Cumulative return | Geometric: `∏(1 + r) − 1` | Correct for multi-period compounding; standard for PM reports |
| Rolling window defaults | 21, 63, 252 days | Short (≈1 M), medium (≈3 M), long (≈1 Y) |
| VaR confidence | 99 % default; 95 % as optional kwarg | Standard risk management convention |
| VaR horizons | 1-day and 10-day | Explicitly listed in roadmap |
| Downside threshold for Sortino | `risk_free` rate (default 0.0) | Consistent with Sharpe signature already in stub |

## Context

The audience is portfolio managers who need daily monitoring of the QIS
strategy and its four subcomponents.  Numbers will later be embedded in an HTML
report (Phase 4), so every function must return a scalar or a `pd.Series` with
a clean `DatetimeIndex` — no opaque objects.

## Out of Scope for This Phase

- Factor attribution and scenario analysis (Phase 2)
- Portfolio-level marginal / component VaR (Phase 3)
- CLI entry point or report rendering (Phase 4)
- Logging, retries, data-quality gates (Phase 5)
- Any data not already in `returns_df`
