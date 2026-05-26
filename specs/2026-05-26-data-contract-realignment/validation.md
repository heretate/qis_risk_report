# Validation — Data Contract Realignment

## Definition of Done

This feature is ready to merge when all of the following pass.

---

## 1. Automated tests

| Check | Command | Pass condition |
|---|---|---|
| Full test suite | `pytest` | 0 failures, 0 errors |
| Linter | `ruff check .` | 0 issues |
| Smoke report | `pytest -m slow` | Exit code 0; HTML > 400 KB; no `factor` / `attribution` section header in output |

---

## 2. DataFrame naming

- `grep -r "returns_df"` returns **zero** hits outside of comments or docstrings.
- `grep -r "portfolio_returns_df"` returns zero hits.
- `qis_return_df` and `portfolio_return_df` are the only DataFrame variable names used in `loaders.py`, `metrics.py`, `scenarios.py`, and the notebook setup cell.

---

## 3. Factor Attribution section absent

- `notebooks/risk_report.ipynb` contains no cell referencing `factors_df`, `build_attribution_table`, or any `plot_*_factor_*` function.
- The generated HTML report does **not** contain the text `Factor Attribution` as a section heading.
- No `factors_path` key in `config/settings.yaml` (or the key is present with a `null` value and a `# deferred` comment).

---

## 4. Scenario Analysis coverage

- Running the smoke test produces an HTML report where:
  - All 5 default scenarios appear in the scenario table.
  - GFC, EUR crisis, CNY rows show `—` (or empty) in portfolio P&L columns.
  - COVID and 2022 rate shock rows show numeric portfolio P&L values.
- `run_scenario` unit test: calling with `portfolio_return_df=None` returns a `ScenarioResult` where all portfolio fields are `None`, and no exception is raised.

---

## 5. Portfolio Risk Contribution grid

- `build_portfolio_contribution_grid` unit test: given a 5-day fixture with two assets (QIS + one portfolio instrument), calling with `weights_list=[0.01, 0.05]` returns a 2-row DataFrame with the expected columns and no NaN values.
- The generated HTML report contains the sensitivity grid table with at least 4 rows (one per configured `hypothetical_qis_weights` entry).
- The `plot_allocation_sensitivity` figure is present in the HTML (at least 1 `<img>` tag in the Portfolio section).
- `weights_df` is read without error; no code path attempts to use historical weights.

---

## 6. Date range handling

- `common_date_range` unit test: given `qis_return_df` starting 2008 and `portfolio_return_df` starting 2020, the returned range starts on or after 2020-01-01.
- No function in `metrics.py` or `scenarios.py` raises an index-alignment error when passed both DataFrames.

---

## Merge blockers

- Any reference to the old DataFrame names (`returns_df`, `portfolio_returns_df`) in runnable code.
- The Factor Attribution section appearing in the generated HTML.
- `pytest` failures on renamed fixture paths.
- `portfolio_return_df` data before 2020 being loaded or assumed in any computation.
