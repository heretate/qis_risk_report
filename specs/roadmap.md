# Roadmap

Phases are ordered by dependency: each phase unlocks the next. Scope within a phase can be parallelised.

> **Convention — additional data requirements:** If any phase or task requires data not already defined in the Data Contract below, stop and ask before proceeding. Do not assume a schema, invent placeholder data, or silently expand the contract. Describe what is needed, why, and what shape it would take, then wait for confirmation before adding it to the contract or writing any code that depends on it.

---

## Assumed Data Contract

*The data pipeline (Bloomberg/SQL connectors, caching, normalisation) is built separately and out of scope for this project. All phases assume the following pre-built inputs are available — either loaded from flat files or injected by the external pipeline.*

**`returns_df`** — daily returns for each QIS subcomponent and the aggregate strategy:

| Field | Type | Notes |
|---|---|---|
| Index | `pd.DatetimeIndex` | Business-day frequency, tz-naive |
| `<subcomponent>` × 4 | `float64` | Simple daily return per subcomponent (e.g. `0.0012` = +0.12%) |
| `total` | `float64` | Aggregate QIS strategy daily return |

**`portfolio_returns_df`** — daily returns for the broader portfolio (Phase 4 only):

| Field | Type | Notes |
|---|---|---|
| Index | `pd.DatetimeIndex` | Same calendar as `returns_df` |
| `<instrument>` × N | `float64` | Simple daily return per portfolio instrument |
| `qis_total` | `float64` | QIS strategy return, duplicated here for marginal-VaR decomposition |

**`weights_df`** — portfolio weights for each instrument over time (Phase 3 onwards):

| Field | Type | Notes |
|---|---|---|
| Index | `pd.DatetimeIndex` | Business-day frequency, aligned to `portfolio_returns_df` |
| `<instrument>` × N | `float64` | Decimal weight per instrument (e.g. `0.05` = 5%); rows sum to 1.0 |
| `qis_total` | `float64` | Aggregate QIS weight within the broader portfolio |

Weights represent end-of-day positions after any rebalancing. A static allocation may be expressed as a single-row DataFrame broadcast across all dates.

All DataFrames are loaded from CSV at startup via thin helpers (`load_returns`, `load_portfolio`, `load_weights`); paths are specified in `config/settings.yaml`.

---

## Phase 1 — Core Risk Metrics

*Goal: daily risk-return numbers for each QIS subcomponent and the aggregate strategy.*

*Input: `returns_df` as defined above.*

- [x] Return series calculation (daily, cumulative, annualised)
- [x] Volatility (rolling, annualised)
- [x] Sharpe ratio and Sortino ratio
- [x] Maximum drawdown and drawdown duration
- [x] Value-at-Risk: historical simulation and parametric (1-day and 10-day)
- [x] Conditional VaR / Expected Shortfall
- [x] Correlation matrix across the 4 QIS subcomponents
- [x] Unit tests for every metric with known-input / known-output fixtures

---

## Phase 2 — Attribution & Scenario Analysis

*Goal: explain where returns come from and stress-test under adverse conditions.*

*Input: `returns_df`; factor return series (carry, momentum, value, volatility) supplied as additional columns in the same CSV or a separate `factors_df` CSV with the same `DatetimeIndex`.*

- [x] Factor attribution: rolling OLS of each QIS against chosen FX risk factors (carry, momentum, value, volatility)
- [x] Contribution-to-return decomposition across the 4 subcomponents
- [x] Historical scenario replay: P&L impact of past stress events (GFC, COVID, 2022 rate shock, etc.)
- [x] Synthetic scenario engine: user-specified spot / vol / correlation shocks applied to current positions
- [x] `scenarios/` module with a clean API: `run_scenario(portfolio, shock_params) -> ScenarioResult`

---

## Phase 3 — Portfolio Risk Contribution

*Goal: quantify the QIS strategy's marginal risk inside the broader portfolio.*

*Input: `returns_df`, `portfolio_returns_df`, and `weights_df` as defined above.*

- [x] Accept a broader portfolio positions file as additional input
- [x] Load and validate `weights_df`; expose a `load_weights(path) -> pd.DataFrame` helper
- [x] Weight-adjusted risk contribution: scale each instrument's standalone risk by its portfolio weight before decomposition
- [x] Marginal VaR contribution of the QIS strategy to the aggregate book
- [x] Component VaR decomposition (each QIS → strategy → portfolio), weighted by `weights_df`
- [x] Correlation of QIS returns with the rest of the portfolio
- [x] Diversification benefit estimate using weighted covariance

---

## Phase 4 — Report Generation

*Goal: automated, consistently formatted HTML report delivered from a single CLI command.*

*Input: outputs of Phases 1–3; `returns_df` and `portfolio_returns_df` re-loaded from the same CSV paths for reproducibility.*

- [x] Jupyter notebook template (`notebooks/risk_report.ipynb`) with cells for each section (performance, risk, attribution, scenarios, portfolio contribution)
- [x] `papermill` integration: inject `run_date`, `config_path`, and output path as parameters
- [x] `nbconvert` HTML export with a clean stylesheet
- [x] `cli.py` `generate-report` command: load → compute → render → export in one call
- [x] Output naming convention: `reports/risk_report_YYYYMMDD.html`
- [x] Smoke test: run the CLI end-to-end against fixture data and assert a non-empty HTML file is produced

---

## Phase 5 — Automation & Hardening

*Goal: production-grade reliability for daily scheduled runs.*

*Input: same CSV paths as all prior phases; no change to the data contract.*

- [ ] Structured logging (`logging` module) with log rotation; errors surfaced clearly in the CLI exit code
- [ ] Retry logic and clear error messages for missing or malformed input files
- [ ] Data-quality checks: missing dates, stale prices, outlier returns — fail fast with descriptive errors
- [ ] Windows Task Scheduler (or cron) configuration documented in `README`
- [ ] `--dry-run` flag: validates data availability and config without producing a report
- [ ] End-to-end integration test using full fixture dataset
- [ ] Version pinning audit and dependency review

---

## Out of Scope (for now)

- Data pipeline / connectors (Bloomberg, SQL, CSV normalisation) — built externally
- Real-time / intraday monitoring
- Interactive web dashboard
- Automated email distribution of reports
- Multi-user access control
