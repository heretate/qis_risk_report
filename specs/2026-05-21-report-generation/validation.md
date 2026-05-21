# Validation — Phase 4: Report Generation

## Definition of Done

Phase 4 is complete when all of the following pass without manual intervention.

---

## Automated Smoke Test

**Location:** `tests/test_report_generation.py`

**Steps:**

1. Invoke `generate-report` via `click.testing.CliRunner` with:
   - `--config` pointing at a minimal test settings file referencing fixture CSVs in `tests/fixtures/`
   - `--date 2024-01-31` (a date present in fixture data)
2. Assert CLI exit code is `0`.
3. Assert the file `reports/risk_report_20240131.html` exists on disk.
4. Assert file size > 0 bytes.
5. Clean up the generated file after the test (so CI is idempotent).

**Failure modes that must surface as non-zero exits (separate negative tests):**

- `--config` points to a non-existent file → exit code 1.
- Fixture data is intentionally broken (empty CSV) → exit code 2 or 3 with a message on stderr.

---

## Manual Sign-off Checklist

Run once before marking the PR ready for review:

- [ ] `python -m qis_risk_report generate-report --config config/settings.yaml` completes without error on real fixture data.
- [ ] The output HTML file opens in a browser without JavaScript errors.
- [ ] All five sections (Performance, Risk Metrics, Factor Attribution, Scenarios, Portfolio Risk Contribution) are visible with at least one table or chart each.
- [ ] The filename matches `risk_report_YYYYMMDD.html` where YYYYMMDD is today's date.
- [ ] Re-running the command on the same date overwrites the previous file without error.

---

## Merge Criteria

- All `pytest` tests pass (including the new smoke test).
- `ruff check .` reports no errors.
- The manual checklist above is completed and noted in the PR description.
- The Phase 4 roadmap bullets in `specs/roadmap.md` are marked `[x]`.
