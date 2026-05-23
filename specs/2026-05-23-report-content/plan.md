# Plan — Phase 5: Report Content & Visualisations

Each task group is independently implementable once the preceding group's public API is stable. Groups 1–7 can be parallelised after Group 1 is complete.

---

## Group 1 — Chart Utility Module

*Creates the shared foundation all later groups depend on.*

1. Create `src/qis_risk_report/reports/charts.py`.
2. Define a module-level `PALETTE` dict mapping `"total"` and each subcomponent name to a fixed color (use `seaborn.color_palette("tab10")`).
3. Implement `apply_style(fig, ax)` — sets consistent font sizes, grid style, spine removal. Call at the end of every chart function.
4. Implement `subcomponent_names(returns_df) -> list[str]` — returns the non-`total` columns in order; used by all chart functions to avoid hard-coding names.
5. Add `charts.py` to the module's `__init__.py` exports.

---

## Group 2 — Report Header (KPI Strip)

1. Implement `build_headline_kpis(returns_df, run_date, risk_free_rate=0.0) -> pd.DataFrame` in `charts.py`.
   - Returns a single-row DataFrame with columns: `YTD Return`, `1Y Ann. Return`, `Ann. Vol (1Y)`, `Sharpe (1Y)`, `Max Drawdown`, `Current Drawdown`, `1D VaR 99%`.
   - Delegates to existing Phase 1 metric functions; no new computation logic here.
2. Add a notebook cell at the top of `notebooks/risk_report.ipynb` (after the parameters cell) that calls `build_headline_kpis` and renders it with `display(df.style.format("{:.2%}"))`.

---

## Group 3 — Performance Section

1. Implement `build_performance_table(returns_df, run_date) -> pd.DataFrame`.
   - Columns: series name; 1D, MTD, YTD, 1Y (total return); 1Y Ann.; since inception (total return).
   - Rows: each subcomponent + `total`.
2. Implement `plot_cumulative_returns(returns_df) -> Figure` (chart P-1).
   - Index to 100 at first date; one line per series; legend outside right.
3. Implement `plot_monthly_heatmap(returns_df) -> Figure` (chart P-2).
   - One subplot row per series (5 rows); x-axis = month, y-axis = year; `seaborn.heatmap` with diverging palette.
4. Implement `plot_daily_returns_bar(returns_df, lookback_days=63) -> Figure` (chart P-3).
   - 5 panels with shared x-axis; positive bars green, negative red; 20-day rolling mean overlaid.
5. Wire all three chart functions and the table into the Performance section cells of the notebook.

---

## Group 4 — Risk Metrics Section

1. Implement `build_risk_table(returns_df, run_date, risk_free_rate=0.0) -> pd.DataFrame`.
   - Rows: each subcomponent + `total`; columns per metric as defined in requirements.
   - Delegates to `metrics.py` functions from Phase 1.
2. Implement `plot_rolling_volatility(returns_df, windows=(63, 252)) -> Figure` (chart R-1).
   - One line per series per window; 63-day dashed, 252-day solid.
3. Implement `plot_drawdown(returns_df) -> Figure` (chart R-2).
   - Two panels (shared x-axis): top = cumulative return of `total`, bottom = drawdown depth; trough periods shaded with `axvspan`.
4. Implement `plot_return_distribution(returns_df, window=252) -> Figure` (chart R-3).
   - Faceted: one subplot per series; `sns.histplot` + KDE; VaR 95% and CVaR 95% vertical lines.
5. Implement `plot_correlation_heatmap(returns_df) -> Figure` (chart R-4).
   - 4 subcomponents only (exclude `total`); annotated; `RdBu_r` palette.
6. Implement `plot_rolling_correlation(returns_df, window=252) -> Figure` (chart R-5).
   - 6 pairwise lines; legend lists each pair.
7. Wire into Risk Metrics section cells of the notebook.

---

## Group 5 — Factor Attribution Section

*Depends on `factors_df` being loaded in the notebook's setup cell.*

1. Implement `build_attribution_table(returns_df, factors_df, window=252, run_date=None) -> pd.DataFrame`.
   - Rows: each subcomponent; columns: beta per factor, R², YTD return per factor, residual alpha.
2. Implement `plot_rolling_factor_betas(returns_df, factors_df, window=252) -> dict[str, Figure]` (chart A-1).
   - Returns one Figure per subcomponent keyed by subcomponent name; four factor lines per figure.
3. Implement `plot_attribution_waterfall(returns_df, factors_df, run_date) -> Figure` (chart A-2).
   - Stacked horizontal bars; one bar per subcomponent; segments per factor + residual.
4. Implement `plot_contribution_area(returns_df, window=252) -> Figure` (chart A-3).
   - Area chart; each subcomponent's daily contribution; areas sum to total; trailing `window` days.
5. Wire into Factor Attribution section cells of the notebook; iterate `plot_rolling_factor_betas` result to display all four figures.

---

## Group 6 — Scenario Analysis Section

*Depends on Phase 2 `ScenarioResult` type and `run_scenario` API.*

1. Define `HISTORICAL_SCENARIOS: list[dict]` in `charts.py` — each entry has `name`, `start`, `end` (ISO date strings). Default list: GFC, EUR sovereign debt, CNY devaluation, COVID, 2022 rate shock.
2. Implement `build_scenario_table(scenario_results: list[ScenarioResult]) -> pd.DataFrame`.
   - Rows: one per scenario; columns: name, date range, strategy P&L, per-subcomponent P&L, vol during event.
3. Implement `plot_scenario_bars(scenario_results) -> Figure` (chart S-1).
   - Grouped bars sorted by strategy P&L; `total` bar outlined in black.
4. Implement `plot_stress_path(returns_df, scenario_name, start, end) -> Figure` (chart S-2).
   - Cumulative P&L from `start`; one line per series; title = scenario name.
5. Wire into Scenario Analysis section cells; render S-2 for GFC and COVID by default.
6. Build the synthetic shock sensitivity grid as a DataFrame (rows = spot shocks, columns = vol shocks) from `config/settings.yaml` `synthetic_shocks` block; display with `df.style`.

---

## Group 7 — Portfolio Risk Contribution Section

1. Implement `build_portfolio_contribution_table(marginal_var, component_var, weights_df, returns_df, portfolio_returns_df, run_date, window=252) -> pd.DataFrame`.
   - Single-row summary as specified in requirements.
2. Implement `plot_component_var(component_var_series) -> Figure` (chart C-1).
   - Horizontal bar chart; bars sorted by magnitude; QIS subcomponent bars stacked within the QIS bar.
3. Implement `plot_rolling_qis_portfolio_correlation(returns_df, portfolio_returns_df, window=252) -> Figure` (chart C-2).
   - One bold line for `qis_total`; thinner lines for each subcomponent; y-axis −1 to 1.
4. Implement `plot_diversification_benefit(returns_df, portfolio_returns_df, weights_df, window=252) -> Figure` (chart C-3).
   - Rolling `Σ standalone VaR − portfolio VaR` as % of portfolio VaR; single line; zero reference line.
5. Wire into Portfolio Risk Contribution section cells of the notebook.

---

## Group 8 — Notebook Template Wiring

*Consolidates all groups into the final notebook structure.*

1. Confirm `notebooks/risk_report.ipynb` section order: Setup → Header → Performance → Risk → Attribution → Scenarios → Portfolio.
2. Ensure the Setup cell loads `factors_df` from the path specified in `config/settings.yaml` (add `factors_path` key to settings if not present — stop and confirm with team before expanding the contract).
3. Each section follows the pattern: markdown header cell → data/compute cell → one or more chart/table cells.
4. Verify the notebook executes end-to-end with `papermill` against fixture CSVs without errors.

---

## Group 9 — Smoke Test

1. Add (or update) `tests/test_smoke_report.py`.
2. The test runs `generate-report` against fixture CSVs via `subprocess.run` and asserts exit code 0.
3. Load the output HTML and assert:
   - File size > 500 KB (confirms charts are embedded as base64 PNG).
   - All 5 section headers present (search for the `<h2>` text or notebook cell output).
   - At least 22 `<img` tags present (one per chart defined in requirements).
4. The test is marked `slow` and excluded from the default `pytest` run; use `pytest -m slow` to run it explicitly.
