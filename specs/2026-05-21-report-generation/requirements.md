# Requirements — Phase 4: Report Generation

## Scope

Automated generation of a consistently formatted HTML report from a single CLI command, consuming the outputs of Phases 1–3. No new data inputs are introduced.

---

## Report Sections & Order

The notebook template must contain exactly these sections, in this order:

| # | Section | Source |
|---|---|---|
| 1 | Performance | Phase 1 — return series (daily, cumulative, annualised) |
| 2 | Risk Metrics | Phase 1 — volatility, Sharpe, Sortino, drawdown, VaR, CVaR, correlation |
| 3 | Factor Attribution | Phase 2 — rolling OLS factor attribution, contribution decomposition |
| 4 | Scenarios | Phase 2 — historical scenario replay + synthetic shock results |
| 5 | Portfolio Risk Contribution | Phase 3 — marginal VaR, component VaR, correlation, diversification benefit |

Each section is a separate notebook cell group (markdown header cell + one or more code cells). Section order must not change without updating this document.

---

## Parameterisation Contract

papermill injects exactly three parameters into the notebook's `parameters`-tagged cell:

| Parameter | Type | Description |
|---|---|---|
| `run_date` | `str` (ISO 8601, `YYYY-MM-DD`) | The as-of date for the report; used to filter/slice data and label the output |
| `config_path` | `str` | Absolute or repo-relative path to `config/settings.yaml` |
| `output_path` | `str` | Full path (including filename) where the executed notebook is saved before HTML export |

No other parameters may be injected at this stage. Any future additions require an update to this document and a corresponding change to the notebook's default-values cell.

---

## CLI Flags & Error Handling

Command: `python -m qis_risk_report generate-report`

| Flag | Required | Default | Description |
|---|---|---|---|
| `--config` | Yes | — | Path to `config/settings.yaml` |
| `--date` | No | Today (`YYYY-MM-DD`) | As-of date for the report |
| `--output-dir` | No | `reports/` | Directory where the final HTML is written |

**Exit codes:**

| Code | Condition |
|---|---|
| 0 | Report produced successfully; path printed to stdout |
| 1 | Config file not found or unparseable |
| 2 | Notebook execution failed (papermill error) |
| 3 | HTML export failed (nbconvert error) |

On any non-zero exit, a human-readable error message is printed to stderr. No stack traces are exposed to the user (log the full traceback at DEBUG level only).

---

## Out of Scope for Phase 4

- Custom CSS / branding (use nbconvert built-in theme)
- File versioning or conflict resolution on same-date re-runs (overwrite)
- Email distribution of the generated report
- Interactive / JavaScript charts (static matplotlib/seaborn only)
- `--dry-run` flag (deferred to Phase 5)
