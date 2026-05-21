# Roadmap

Each phase ships a working vertical slice. Later phases extend without breaking earlier ones.

---

## Phase 1 — Core Pipeline (MVP)

**Goal:** End-to-end pipeline from CSV to Excel report; validates the architecture before any external dependencies.

- `data/loaders.py`: `load_csv` and `load_excel` returning a daily-returns `DataFrame`
- `risk/metrics.py`: `RiskMetrics` computing annualized return, volatility, Sharpe ratio, max drawdown, historical VaR
- `reports/generator.py`: `to_excel()` writing a formatted workbook via openpyxl
- `cli.py`: `qis-risk-report generate <file> --format excel`
- `config/settings.yaml`: output directory, date format
- Full unit tests for metrics; integration test for the CSV → Excel path

---

## Phase 2 — HTML & PDF Reports

**Goal:** Parity with Excel; adds read-only presentation-quality reports.

- Jinja2 templates in `reports/templates/`
- `to_html()` and `to_pdf()` on `ReportGenerator`
- CLI `--format html|pdf` options
- Tests covering template rendering with a fixture DataFrame

---

## Phase 3 — Portfolio Risk Contribution

**Goal:** Quantify how the QIS strategy contributes to the broader portfolio's risk.

- Marginal and component VaR relative to a benchmark portfolio
- Correlation and beta to portfolio returns
- New `risk/portfolio.py` module; results surfaced in existing reports

---

## Phase 4 — Subcomponent Attribution

**Goal:** Decompose aggregate strategy performance across the four constituent QIS.

- Per-QIS return, vol, Sharpe, and drawdown columns in reports
- Aggregation vs. individual contribution waterfall
- CLI `--breakdown` flag to toggle subcomponent detail

---

## Phase 5 — Scenario Analysis

**Goal:** Stress-test the strategy and its subcomponents under defined market regimes.

- Historical scenario replay (e.g., COVID drawdown, 2022 rates shock) using date-range slicing
- Synthetic scenario construction (parallel shift, correlation breakdown)
- Scenario results as a separate sheet/section in Excel and HTML reports
- `risk/scenarios.py` module

---

## Phase 6 — Factor Attribution

**Goal:** Explain return drivers via regression on common FX risk factors.

- OLS factor model in `risk/attribution.py` using `statsmodels`
- Factor loadings and R² reported per QIS and for the aggregate strategy
- Attribution table added to all report formats
