# Phase 3 — Portfolio Risk Contribution: Validation

## Definition of Done

Phase 3 is complete and ready to merge when all of the following pass.

## 1. Linter

```bash
ruff check .
```

Zero errors, zero warnings.

## 2. Test Suite

```bash
pytest tests/test_portfolio.py -v
```

All tests green. No skips.

## 3. Data Loaders — Validation Tests

- `load_portfolio` returns a `pd.DataFrame` with a `pd.DatetimeIndex` and a `qis_total` column on a valid CSV.
- `load_portfolio` raises `FileNotFoundError` with a descriptive message when the path does not exist.
- `load_portfolio` raises `ValueError` when `qis_total` is absent.
- `load_weights` returns a `pd.DataFrame` with a `pd.DatetimeIndex` and a `qis_total` column on a valid CSV.
- `load_weights` raises `FileNotFoundError` when the path does not exist.
- `load_weights` raises `ValueError` when any row does not sum to `1.0 ± 1e-6`.

## 4. Marginal VaR — Known-Output Fixtures

- `marginal_var` is run on `tests/fixtures/portfolio_returns.csv` and `tests/fixtures/weights.csv`.
- Output Series values match `tests/fixtures/marginal_var_expected.csv` within `1e-6` absolute tolerance per instrument.
- Values sum to `portfolio_var` (at the same confidence level) within `1e-8` absolute tolerance.

## 5. Component VaR — Known-Output Fixtures

- `component_var` is run on the same fixtures.
- Output Series values match `tests/fixtures/component_var_expected.csv` within `1e-6` absolute tolerance per instrument.
- Values sum to `portfolio_var` within `1e-8` absolute tolerance.

## 6. QIS-Portfolio Correlation — Known-Output Fixtures

- `qis_portfolio_correlation` is run on `tests/fixtures/portfolio_returns.csv` and `tests/fixtures/portfolio_returns.csv` (acting as the portfolio aggregate stand-in).
- Output Series values match `tests/fixtures/portfolio_correlation_expected.csv` within `1e-6` absolute tolerance.
- All correlation values are in the range `[-1.0, 1.0]`.

## 7. Diversification Benefit — Behavioural Tests

- Result is a non-negative scalar for well-formed inputs.
- Result equals `Σ(w_i × standalone_VaR_i) − portfolio_var` within `1e-8` tolerance.
- A portfolio of perfectly correlated instruments produces a diversification benefit of approximately zero.
- `ValueError` is raised (not silently returned) when degenerate inputs produce a negative result.

## Merge Gate

All items above must be checked before opening a PR to `main`. The PR description must link to this file.
