# Tech Stack

## Runtime

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.10+ | Team standard; strong quant ecosystem |
| Dependency management | pip + `requirements.txt` | Team standard; no additional toolchain needed |
| Entry point | CLI via `click` | Scheduled via Windows Task Scheduler or cron; human-runnable |

## Data Layer

| Concern | Library / Tool |
|---|---|
| Bloomberg real-time / historical data | `blpapi` (Bloomberg Python API) |
| SQL databases (positions, P&L, reference) | `SQLAlchemy` + `pyodbc` or `psycopg2` depending on engine |
| CSV / flat-file ingestion | `pandas.read_csv` with configurable path/glob patterns |
| Data modeling & transformation | `pandas`, `numpy` |

Connection credentials and DSNs are managed through environment variables or a `config/settings.yaml` file, never hard-coded.

## Risk & Analytics

| Concern | Library |
|---|---|
| Core numerics | `numpy`, `scipy` |
| Time-series risk metrics (VaR, vol, Sharpe, drawdown) | `pandas` + custom `risk/` module |
| Factor attribution | `statsmodels` (OLS / rolling regression) |
| Scenario analysis (historical + synthetic) | custom `scenarios/` module built on `pandas` |
| Portfolio-level risk contribution | custom module using covariance decomposition |

## Reporting

| Concern | Library / Tool |
|---|---|
| Report authoring | Jupyter Notebook (`.ipynb` templates) |
| HTML rendering | `nbconvert` (`--to html`) |
| Charts & visualisations | `matplotlib`, `seaborn`; optionally `plotly` for interactivity |
| Table formatting | `jinja2` for HTML snippets inside notebooks |
| Parameterisation | `papermill` to inject run-date and config into notebook before execution |

## Testing & Quality

| Concern | Tool |
|---|---|
| Unit & integration tests | `pytest` |
| Fixtures / mock data | `pytest` fixtures + small CSV snapshots committed to `tests/fixtures/` |
| Linting | `ruff` |
| Type hints | `mypy` (optional, incremental) |

## Project Layout (target)

```
qis_risk_report/
├── config/
│   └── settings.yaml          # DSNs, paths, strategy metadata
├── notebooks/
│   └── risk_report.ipynb      # Parameterised report template
├── src/qis_risk_report/
│   ├── cli.py                 # click entry point
│   ├── data/                  # bloomberg.py, sql.py, loaders.py
│   ├── risk/                  # metrics.py, attribution.py, scenarios.py
│   └── reports/               # generator.py (papermill + nbconvert)
├── tests/
├── requirements.txt
└── pyproject.toml
```
