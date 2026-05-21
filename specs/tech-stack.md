# Tech Stack

## Language & Runtime

- **Python 3.11+** — type-hint support, `tomllib` stdlib, performance improvements
- **pyproject.toml** (setuptools) — single source for metadata, deps, and entry points

## Data Ingestion

| Source | Library | Notes |
|---|---|---|
| CSV / Excel files | `pandas` | `read_csv` / `read_excel`; thin loader wrappers in `data/loaders.py` |
| Bloomberg Terminal / B-PIPE | `blpapi` | Optional extra; context-manager client in `data/bloomberg.py` |

## Risk Computation

| Metric | Library |
|---|---|
| Annualized return, volatility, Sharpe | `numpy`, `pandas` |
| Max drawdown | `pandas` (cumulative max rolling) |
| VaR (historical) | `numpy.percentile` |
| Factor attribution (future) | `statsmodels` OLS |

## Report Generation

Both output formats are first-class deliverables.

| Format | Library | Template |
|---|---|---|
| Excel | `openpyxl` | Programmatic sheets; no Jinja2 |
| HTML | `Jinja2` | Templates in `reports/templates/` |
| PDF | `WeasyPrint` | Rendered from the same HTML template |

`ReportGenerator` exposes `to_excel()`, `to_html()`, and `to_pdf()` from a single class.

## CLI

- **Click** — `qis-risk-report generate <file> [--format excel|html|pdf]`

## Configuration

- **PyYAML** — `config/settings.yaml` (committed) + `config/settings.local.yaml` (gitignored override)

## Testing & Quality

| Tool | Purpose |
|---|---|
| `pytest` | Unit and integration tests |
| `pytest-cov` | Coverage reporting |
| `ruff` | Lint + format (replaces flake8, isort, black) |
| `mypy` | Static type checking |

## Optional / Future

- `statsmodels` — regression-based factor attribution
- `scipy` — parametric VaR, CVaR, correlation matrices
- `matplotlib` / `plotly` — embedded charts in HTML reports
