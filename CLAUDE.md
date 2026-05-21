# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**qis_risk_report** is a Python CLI tool that ingests portfolio returns data (CSV/Excel or Bloomberg), computes standard QIS risk metrics, and generates reports in Excel, HTML, or PDF format.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"           # core + dev tools
pip install -e ".[dev,bloomberg]" # also install blpapi
```

Bloomberg support requires a running Bloomberg Terminal or B-PIPE on `localhost:8194`. The `blpapi` package must be installed separately from Bloomberg's developer portal if the PyPI wheel doesn't work.

## Common commands

```powershell
# Run all tests
pytest

# Run a single test file
pytest tests/test_metrics.py

# Run a single test
pytest tests/test_metrics.py::test_summary_shape

# Lint + format check
ruff check src tests
ruff format --check src tests

# Type check
mypy src

# Generate a report from a CSV
qis-risk-report generate data/input/returns.csv --format excel
```

## Architecture

```
src/qis_risk_report/
├── data/
│   ├── loaders.py      # load_csv / load_excel — thin wrappers around pandas
│   └── bloomberg.py    # BloombergClient — context-manager wrapping blpapi
├── risk/
│   └── metrics.py      # RiskMetrics — takes a returns DataFrame, exposes .summary()
├── reports/
│   └── generator.py    # ReportGenerator — to_excel / to_html / to_pdf
└── cli.py              # Click CLI; entry point: qis-risk-report generate <file>
```

### Data flow

1. **Ingest** — `data/loaders.py` or `data/bloomberg.py` produce a `pd.DataFrame` of daily returns (dates as index, assets as columns).
2. **Compute** — `risk/metrics.py` `RiskMetrics` takes that DataFrame and computes annualized return, volatility, Sharpe, max drawdown, VaR.
3. **Render** — `reports/generator.py` `ReportGenerator` writes to Excel (openpyxl) or renders a Jinja2 template to HTML/PDF (WeasyPrint).

### Configuration

`config/settings.yaml` holds Bloomberg connection params, output directory, and date format. A `config/settings.local.yaml` (gitignored) can override any value for local development.

### Bloomberg client

`BloombergClient` is a stub — `get_reference_data` and `get_historical_data` are `NotImplementedError` placeholders to be implemented against the actual blpapi event loop. Use it as a context manager to ensure `disconnect()` is called.

### Report templates

HTML/PDF reports use Jinja2 templates stored in `src/qis_risk_report/reports/templates/`. The template directory is passed to `ReportGenerator` at construction time. Templates receive whatever `context` dict the caller supplies.

## Output

Generated reports go to `output/` (gitignored). The directory is created automatically by `ReportGenerator`.
