# Phase 3 — Portfolio Risk Contribution: Requirements

## Scope

Implement portfolio-level risk decomposition: load and validate the two new DataFrames (`portfolio_returns_df`, `weights_df`), compute weight-adjusted risk contributions, marginal VaR, component VaR, QIS-portfolio correlation, and diversification benefit.

## Data Contract Additions

Both DataFrames are already defined in `specs/roadmap.md`. No new fields are required.

**`portfolio_returns_df`** — daily returns for the broader portfolio instruments:

| Field | Type | Notes |
|---|---|---|
| Index | `pd.DatetimeIndex` | Business-day frequency, tz-naive, aligned to `returns_df` |
| `<instrument>` × N | `float64` | Simple daily return per instrument |
| `qis_total` | `float64` | QIS strategy return, duplicated for marginal-VaR decomposition |

**`weights_df`** — portfolio weights per instrument over time:

| Field | Type | Notes |
|---|---|---|
| Index | `pd.DatetimeIndex` | Aligned to `portfolio_returns_df` |
| `<instrument>` × N | `float64` | Decimal weight per instrument; rows sum to 1.0 |
| `qis_total` | `float64` | Aggregate QIS weight within the broader portfolio |

A static allocation may be expressed as a single-row DataFrame broadcast across all dates.

Loaded via new helpers `load_portfolio(path)` and `load_weights(path)` in `src/qis_risk_report/data/loaders.py`; paths added to `config/settings.yaml`.

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Marginal VaR method | Parametric covariance-based: `ΔVAR_i = (Cov(r_i, r_P) / σ_P) × z × w_i` | Closed-form, consistent with Phase 1 parametric VaR; avoids resampling overhead |
| Component VaR formula | `CVaR_i = ρ(r_i, r_P) × VaR_standalone_i × w_i` | Standard covariance decomposition; component VaRs sum to portfolio VaR |
| VaR confidence level | 95% (consistent with Phase 1) | Report consistency |
| Covariance estimation | Historical covariance on the full aligned date range | Matches Phase 1 approach; no EWMA for MVP |
| Weights handling | Use the most recent row of `weights_df` as current; validate rows sum to 1.0 ± 1e-6 | Simplest correct behaviour; static allocations degenerate naturally |
| Diversification benefit | `Σ(w_i × standalone_VaR_i) − portfolio_VaR` | Intuitive for PMs; expressed in return space (same units as VaR) |

## Out of Scope for Phase 3

- Bloomberg / SQL connectors (data pipeline is external)
- EWMA or other dynamic covariance estimators
- Report rendering (Phase 4)
- Intraday or real-time risk contribution

## File Structure

```
src/qis_risk_report/
├── data/
│   └── loaders.py           # add load_portfolio(), load_weights()
└── risk/
    └── portfolio.py          # marginal_var(), component_var(), qis_portfolio_correlation(), diversification_benefit()
tests/
├── test_portfolio.py
└── fixtures/
    ├── portfolio_returns.csv
    ├── weights.csv
    ├── marginal_var_expected.csv
    ├── component_var_expected.csv
    └── portfolio_correlation_expected.csv
config/
└── settings.yaml             # add portfolio_returns_path, weights_path
```

## Context

Phases 1 and 2 are complete. Phase 3 shifts focus from the QIS strategy in isolation to its role inside the broader portfolio — the core PM question is "how much risk does the QIS add to the book?" Phase 4 (report generation) will call Phase 3 functions directly from the notebook template. Keeping the API surface small and purely functional (no side-effects, returns DataFrames or scalars) ensures it is easy to wire in.
