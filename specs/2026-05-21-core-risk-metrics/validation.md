# Validation — Phase 1: Core Risk Metrics

This phase is complete and ready to merge when **all three** criteria below are
satisfied.

---

## 1. No stub remains

```
grep -r "NotImplementedError" src/qis_risk_report/risk/metrics.py
```

Must return **no output**.  Every function body must contain a real
implementation, not a `raise NotImplementedError`.

---

## 2. All unit tests pass

```
pytest tests/test_metrics.py -v
```

Expected output: all tests `PASSED`, zero failures, zero errors.

Each of the following must have at least one passing test:

| Metric | Function |
|---|---|
| Cumulative return | `cumulative_return` |
| Annualised return | `annualised_return` |
| Volatility (full + rolling) | `annualised_volatility` |
| Sharpe ratio | `sharpe_ratio` |
| Sortino ratio | `sortino_ratio` |
| Drawdown series | `drawdown_series` |
| Maximum drawdown | `max_drawdown` |
| Drawdown duration | `drawdown_duration` |
| Historical VaR (1-day, 10-day) | `historical_var` |
| Parametric VaR (1-day, 10-day) | `parametric_var` |
| CVaR / Expected Shortfall | `expected_shortfall` |
| Correlation matrix | `correlation_matrix` |

Tests use `pytest.approx` for all float comparisons; expected values are
hand-calculated from the fixture CSVs in `tests/fixtures/`.

---

## 3. Lint passes clean

```
ruff check .
```

Must return **no output** (exit code 0).  Do not suppress rules; fix the
underlying issue.

---

## Not required for merge

- Manual cross-check against Excel / Bloomberg (deferred to Phase 4 when real
  data flows through the report)
- CLI wiring or notebook integration (Phase 4)
- Logging or data-quality gates (Phase 5)
