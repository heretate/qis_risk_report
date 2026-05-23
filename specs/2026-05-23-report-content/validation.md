# Validation — Phase 5: Report Content & Visualisations

## Definition of Done

The phase is complete and ready to merge when **all** criteria below pass. The primary gate is the end-to-end smoke test; the checklist items are the constituent checks that make the smoke test meaningful.

---

## Primary Gate — End-to-End Smoke Test

Run the full report pipeline against fixture CSVs:

```bash
pytest tests/test_smoke_report.py -m slow -v
```

This test must:

1. Exit with code 0 (no pipeline errors).
2. Produce an HTML file at the expected path (`reports/risk_report_YYYYMMDD.html`).
3. Assert HTML file size > 500 KB (confirms charts are embedded, not empty placeholders).
4. Assert the HTML contains all 5 section headers (exact `<h2>` text as written in the notebook markdown cells).
5. Assert the HTML contains ≥ 22 `<img` tags (one per named chart in requirements).

---

## Chart Presence Checklist

Each chart below must be rendered and embedded in the HTML output. Verify by inspecting the HTML file (`BeautifulSoup` in the smoke test, or manually opening in a browser).

### Section 0 — Header
- [x] KPI strip table is present and all 7 columns are non-null

### Section 1 — Performance
- [x] P-1: Cumulative return chart (1 figure, 5 lines)
- [x] P-2: Monthly heatmap (1 figure, 5 subplot rows)
- [x] P-3: Daily return bar chart (1 figure, 5 panels)
- [x] Performance summary table (6 columns × 5 rows minimum)

### Section 2 — Risk Metrics
- [x] R-1: Rolling volatility chart (two windows visible)
- [x] R-2: Drawdown chart (two panels)
- [x] R-3: Return distribution (5 subplots, VaR lines present)
- [x] R-4: Correlation heatmap (4×4 annotated grid)
- [x] R-5: Rolling pairwise correlation (6 lines)
- [x] Risk summary table (9 metrics × 5 series minimum)

### Section 3 — Factor Attribution
- [x] A-1: Rolling factor betas — 4 figures (one per subcomponent)
- [x] A-2: YTD attribution stacked bar (4 bars + legend)
- [x] A-3: Subcomponent contribution area chart
- [x] Attribution summary table (factor betas, R², attributed YTD, alpha)

### Section 4 — Scenario Analysis
- [x] S-1: Scenario impact bar chart (5 scenario groups)
- [x] S-2: GFC stress path chart
- [x] S-2: COVID stress path chart
- [x] Historical scenarios table (5 rows, 7+ columns)
- [x] Synthetic shock sensitivity grid (rendered as styled DataFrame)

### Section 5 — Portfolio Risk Contribution
- [x] C-1: Component VaR horizontal bar chart
- [x] C-2: Rolling QIS–portfolio correlation (5 lines)
- [x] C-3: Diversification benefit over time (1 line + zero reference)
- [x] Portfolio contribution summary table (6 metrics)

**Total: 22 charts + 4 tables + 1 KPI strip**

---

## Metric Spot-Checks

Run the following manual checks against the fixture data where expected values are known. These do not need automated assertions but must be visually confirmed before the PR is merged.

| Check | How to verify |
|---|---|
| Cumulative return in P-1 starts at 100 for all series | Inspect chart at inception date |
| Monthly heatmap uses a diverging palette centred at 0% (white) | Visually confirm a near-zero month cell is white or very light |
| Rolling vol lines in R-1 show the 63-day line more volatile than the 252-day line | Inspect chart; 63-day should show more variance |
| Correlation heatmap diagonal is 1.0 for all series | Read annotated values |
| Scenario P&L in S-1 for GFC is negative for at least the `total` series | Inspect bar chart |
| KPI strip Sharpe ratio is computed with the configured `risk_free_rate` | Check `config/settings.yaml` value vs. displayed number |

---

## Regression Guard

After merging, re-run the existing Phase 1–4 tests to confirm no regressions:

```bash
pytest tests/ -m "not slow" -v
```

All previously passing tests must continue to pass.

---

## Merge Criteria Summary

| Criterion | Gate |
|---|---|
| Smoke test passes (`pytest -m slow`) | Automated — must be green |
| All 22 charts present in HTML | Automated (img tag count) |
| All 5 section headers present | Automated (HTML text search) |
| HTML > 500 KB | Automated |
| Metric spot-checks pass | Manual sign-off by reviewer |
| No regressions in Phase 1–4 tests | Automated — must be green |
| `ruff check .` clean | Automated — must be green |
