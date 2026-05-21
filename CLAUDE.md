# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QIS Risk Report generates analytics and risk monitoring for a pre-defined FX QIS (Quantitative Investment Strategy) and its 4 subcomponents. Output is a daily HTML report for portfolio managers. The codebase is currently in the specification phase — no implementation exists yet.

## Tech Stack

- **Python 3.10+**, pip + `requirements.txt`
- **CLI**: `click` (entry point: `cli.py generate-report`)
- **Analytics**: `pandas`, `numpy`, `scipy`, `statsmodels`
- **Reporting**: Jupyter notebooks + `papermill` (parameterisation) + `nbconvert` (HTML export)
- **Charts**: `matplotlib`, `seaborn` (optionally `plotly`)
- **Testing**: `pytest` with CSV fixture snapshots in `tests/fixtures/`
- **Linting**: `ruff`

## Target Project Layout

```
qis_risk_report/
├── config/settings.yaml          # DSNs, file paths, strategy metadata
├── notebooks/risk_report.ipynb   # Parameterised report template
├── src/qis_risk_report/
│   ├── cli.py                    # click entry point
│   ├── data/                     # loaders.py, bloomberg.py, sql.py
│   ├── risk/                     # metrics.py, attribution.py, scenarios.py
│   └── reports/                  # generator.py (papermill + nbconvert)
├── tests/
│   └── fixtures/                 # Small CSV snapshots for unit tests
├── requirements.txt
└── pyproject.toml
```

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run linter
ruff check .

# Run tests
pytest

# Run a single test file
pytest tests/test_metrics.py

# Generate report (Phase 4+)
python -m qis_risk_report generate-report --config config/settings.yaml

# Dry-run without producing output (Phase 5+)
python -m qis_risk_report generate-report --dry-run
```

## Data Contract

All phases consume pre-built DataFrames loaded from CSV at startup via thin helpers (`load_returns`, `load_portfolio`, `load_weights`). Paths are in `config/settings.yaml`. **Never assume a new schema or silently expand the contract** — if new data is needed, stop and describe what is needed and why before writing any code that depends on it.

| DataFrame | Contents | Phases |
|---|---|---|
| `returns_df` | Daily returns for 4 QIS subcomponents + `total`; `pd.DatetimeIndex`, tz-naive | All |
| `portfolio_returns_df` | Daily returns for broader portfolio instruments + `qis_total` | 3+ |
| `weights_df` | Portfolio weights per instrument; rows sum to 1.0 | 3+ |

Factor data (carry, momentum, value, volatility) is supplied as additional columns in `returns_df` or a separate `factors_df` CSV with the same `DatetimeIndex`.

## Implementation Roadmap

Phases are ordered by dependency; scope within a phase can be parallelised.

- **Phase 1** — Core risk metrics: returns, volatility, Sharpe, Sortino, drawdown, VaR (historical + parametric), CVaR/ES, correlation matrix
- **Phase 2** — Attribution & scenario analysis: rolling OLS factor attribution, contribution decomposition, historical stress scenarios, synthetic shock engine (`scenarios/` module)
- **Phase 3** — Portfolio risk contribution: marginal VaR, component VaR, correlation and diversification benefit vs. broader portfolio
- **Phase 4** — Report generation: notebook template, papermill injection, nbconvert HTML export, `generate-report` CLI command, output naming `reports/risk_report_YYYYMMDD.html`
- **Phase 5** — Hardening: structured logging, retry logic, data-quality checks (missing dates, stale prices, outlier returns), `--dry-run` flag, Task Scheduler docs

## Key Conventions

- Credentials and DSNs go in environment variables or `config/settings.yaml`, never hard-coded.
- Data pipeline (Bloomberg/SQL connectors) is built externally and out of scope — all code assumes pre-built CSVs.
- Every risk metric in Phase 1 requires a unit test with known-input / known-output CSV fixtures.
- The `scenarios/` module exposes a clean API: `run_scenario(portfolio, shock_params) -> ScenarioResult`.
- Report output naming: `reports/risk_report_YYYYMMDD.html`.
