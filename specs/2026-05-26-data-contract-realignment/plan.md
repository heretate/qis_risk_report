# Plan — Data Contract Realignment

Groups are ordered by dependency. Groups 1–2 must complete before the others; Groups 3–6 can be parallelised once the renamed types are stable.

---

## Group 1 — Rename DataFrames throughout the codebase

*All downstream work depends on this rename being complete.*

1. Rename `returns_df` → `qis_return_df` everywhere: `loaders.py`, `cli.py`, `metrics.py`, `attribution.py`, `scenarios.py`, notebook setup cell, all tests.
2. Rename `portfolio_returns_df` → `portfolio_return_df` everywhere (same scope as above).
3. Update `config/settings.yaml`: rename keys `returns_path` → `qis_returns_path` and `portfolio_returns_path` → `portfolio_returns_path` (keep path value; only rename key for clarity if needed).
4. Update fixture CSV paths and any hardcoded column references in `tests/fixtures/`.
5. Run `pytest` to confirm no regressions from the rename alone.

---

## Group 2 — Update data loaders for mismatched date ranges

1. Update `loaders.py` `load_returns` to load `qis_return_df` (path from `qis_returns_path`).
2. Update `loaders.py` `load_portfolio` to load `portfolio_return_df` (path from `portfolio_returns_path`); document that this starts 2020.
3. Add a helper `common_date_range(qis_return_df, portfolio_return_df) -> tuple[pd.Timestamp, pd.Timestamp]` that returns the overlapping date range (2020 onwards) — used by functions that need both DataFrames aligned.
4. Do **not** attempt to back-fill or synthesise portfolio data before 2020.

---

## Group 3 — Remove Factor Attribution section

1. Delete `build_attribution_table`, `plot_rolling_factor_betas`, `plot_attribution_waterfall`, `plot_contribution_area` from `charts.py` (or comment-gate them if already partially implemented).
2. Remove the Factor Attribution section cells from `notebooks/risk_report.ipynb`.
3. Remove `factors_df` loading from the notebook setup cell.
4. Remove `factors_path` from `config/settings.yaml` (or leave the key with a `null` value and a comment noting it is deferred).
5. Delete or skip any unit tests that depend on `factors_df`.
6. Update `tests/test_smoke_report.py` expected section count and `<img>` count to exclude attribution charts.

---

## Group 4 — Scenario Analysis: QIS-only for pre-2020 events

1. In `scenarios.py`, update `run_scenario` to accept an optional `portfolio_return_df` parameter (default `None`).
2. When `portfolio_return_df` is `None` or the scenario date range predates 2020, compute and return QIS metrics only; set portfolio P&L fields to `None`.
3. In `charts.py`, update `build_scenario_table` to render `None` portfolio fields as `—` (em dash) in the HTML output.
4. Update `plot_scenario_bars` to omit portfolio bars when the value is `None` (QIS bars still render).
5. Keep the default 5 historical scenarios unchanged (GFC, EUR crisis, CNY, COVID, 2022 rate shock).
6. Update scenario fixture CSVs to reflect the new shape (some portfolio columns can be absent for pre-2020 events).

---

## Group 5 — Portfolio Risk Contribution: hypothetical allocation sensitivity grid

1. Add `hypothetical_qis_weights: [0.01, 0.025, 0.05, 0.10]` to `config/settings.yaml`.
2. In `metrics.py` or a new `portfolio.py` helper, implement `compute_portfolio_contribution_at_weight(qis_return_df, portfolio_return_df, weights_df, qis_weight) -> dict` which:
   - Constructs a hypothetical blended portfolio return series over the `common_date_range` (Group 2 helper) using `qis_weight` for the QIS total and scales non-QIS weights proportionally so they sum to `1 - qis_weight`.
   - Returns: standalone VaR (QIS), marginal VaR, component VaR share, trailing correlation, diversification benefit.
3. Implement `build_portfolio_contribution_grid(qis_return_df, portfolio_return_df, weights_df, weights_list) -> pd.DataFrame`:
   - Rows: each hypothetical weight level.
   - Columns: the five metrics from step 2.
4. In `charts.py`, replace `build_portfolio_contribution_table` with this grid builder.
5. Add `plot_allocation_sensitivity(grid_df) -> Figure` — line chart; x-axis = QIS weight %, y-axis = metric value; one line per metric (use secondary y-axis or normalise); for the report we want at minimum component VaR share and diversification benefit lines.
6. Update the Portfolio Risk Contribution section in the notebook to call the grid builder and `plot_allocation_sensitivity`.
7. Remove `plot_diversification_benefit` and `plot_rolling_qis_portfolio_correlation` from the portfolio section (they assumed non-zero historical weights); the rolling correlation chart (`C-2`) can remain but must be computed only over the 2020-onward overlap window.

---

## Group 6 — Update tests and fixtures

1. Add/update `tests/fixtures/qis_returns.csv` (rename from `returns.csv` if it existed).
2. Add/update `tests/fixtures/portfolio_returns.csv` — only post-2020 rows.
3. Add a fixture for the sensitivity grid output (known-input/known-output): a two-weight grid (1%, 5%) with a 5-row date range for deterministic checks.
4. Update `tests/test_metrics.py` and `tests/test_attribution.py` to use new DataFrame names.
5. Update `tests/test_smoke_report.py`: adjust expected section headers (4 instead of 5) and `<img>` tag count.

---

## Group 7 — Smoke test and documentation

1. Run the full `pytest` suite; fix any remaining failures.
2. Run `papermill` against updated fixture CSVs end-to-end; confirm HTML output has no missing section references.
3. Update `CLAUDE.md` data contract table to reflect the new DataFrame names and date ranges.
4. Annotate `config/settings.yaml` with comments explaining `hypothetical_qis_weights` and the deferred `factors_path` key.
