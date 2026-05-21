# Plan — Phase 4: Report Generation

Task groups mirror the Phase 4 roadmap bullets. Each group is independently completable once its prerequisites are met.

---

## Group 1 — Notebook Template

1. Create `notebooks/risk_report.ipynb` with a cell for each report section in order: Performance, Risk Metrics, Factor Attribution, Scenarios, Portfolio Risk Contribution.
2. Tag the first code cell as `parameters` (papermill convention) with placeholders: `run_date`, `config_path`, `output_path`.
3. Wire each section cell to call the corresponding Phase 1–3 functions and render output (tables + charts) inline.

**Depends on:** Phases 1–3 implementations.

---

## Group 2 — Papermill Integration

1. Create `src/qis_risk_report/reports/generator.py`.
2. Implement `execute_notebook(config_path, run_date, output_path)`: calls `papermill.execute_notebook` injecting the three parameters.
3. Ensure the executed notebook is saved to a temp path (not the template) so the template stays clean.

**Depends on:** Group 1.

---

## Group 3 — nbconvert HTML Export

1. Extend `generator.py` with `export_html(executed_nb_path, html_output_path)`: calls `nbconvert` programmatically (`HTMLExporter`) or via subprocess.
2. Apply a clean stylesheet (built-in `lab` or `classic` nbconvert theme; no custom CSS at this stage).
3. Return the path of the written HTML file.

**Depends on:** Group 2.

---

## Group 4 — CLI Command

1. In `src/qis_risk_report/cli.py`, add a `generate-report` click command.
2. Flags: `--config` (required, path to `config/settings.yaml`), `--date` (optional, defaults to today), `--output-dir` (optional, defaults to `reports/`).
3. Command flow: load config → resolve paths → call `execute_notebook` → call `export_html` → print confirmation with output path.
4. Exit code 0 on success; non-zero with a clear error message on any failure.

**Depends on:** Groups 2–3.

---

## Group 5 — Output Naming Convention

1. Enforce `reports/risk_report_YYYYMMDD.html` naming in `generator.py` (not in the CLI caller).
2. Create `reports/` directory if it does not exist.
3. If a file with the same name already exists, overwrite it (no versioning at this stage).

**Depends on:** Group 3.

---

## Group 6 — Smoke Test

1. Add `tests/test_report_generation.py`.
2. Fixture: small fixture CSVs already present in `tests/fixtures/`; a minimal `settings.yaml` pointing at them.
3. Test: invoke `generate-report` via `click.testing.CliRunner` → assert exit code 0 → assert `reports/risk_report_YYYYMMDD.html` exists → assert file size > 0.
4. Clean up the generated file after the test.

**Depends on:** Groups 1–5.
