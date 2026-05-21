# Plan — Phase 1: Core Risk Metrics

Each task group is independently implementable.  Groups 1–8 implement the
metrics; group 9 creates the test fixtures; group 10 writes the tests.
Run `pytest` and `ruff check .` to confirm completion.

---

## 1. Return series

File: `src/qis_risk_report/risk/metrics.py`

1.1  `cumulative_return(returns: pd.Series) -> pd.Series`
     Geometric cumulative return at each date: `(1 + r).cumprod() − 1`.

1.2  `annualised_return(returns: pd.Series) -> float`
     Geometric annualised: `(1 + total_cumulative_return) ^ (252 / n) − 1`.

---

## 2. Volatility

File: `src/qis_risk_report/risk/metrics.py`

2.1  `annualised_volatility(returns: pd.Series, window: int | None = None) -> float | pd.Series`
     If `window` is `None`, return a single float (full-period).
     If `window` is given (e.g. 21, 63, 252), return a rolling `pd.Series`.
     Annualise by `× √252`.

---

## 3. Risk-adjusted ratios

File: `src/qis_risk_report/risk/metrics.py`

3.1  `sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float`
     `(annualised_return − risk_free) / annualised_volatility`.

3.2  `sortino_ratio(returns: pd.Series, risk_free: float = 0.0) -> float`
     Replace the denominator with annualised downside deviation
     (standard deviation of returns below `risk_free`).

---

## 4. Drawdown

File: `src/qis_risk_report/risk/metrics.py`

4.1  `drawdown_series(returns: pd.Series) -> pd.Series`
     At each date: `wealth / running_max − 1`.  Used internally and exposed
     for charting.

4.2  `max_drawdown(returns: pd.Series) -> float`
     Minimum value of `drawdown_series`.

4.3  `drawdown_duration(returns: pd.Series) -> int`
     Length in calendar days of the longest drawdown period (peak-to-trough
     measured to the last date at or below the prior peak).

---

## 5. Historical VaR

File: `src/qis_risk_report/risk/metrics.py`

5.1  `historical_var(returns: pd.Series, confidence: float = 0.99, horizon: int = 1) -> float`
     Sort returns ascending; take the `(1 − confidence)` quantile.
     Scale to `horizon` days via `× √horizon`.
     Return as a **positive** number (loss magnitude).

---

## 6. Parametric VaR

File: `src/qis_risk_report/risk/metrics.py`

6.1  `parametric_var(returns: pd.Series, confidence: float = 0.99, horizon: int = 1) -> float`
     Assume normally distributed returns.
     `VaR = −(μ − z × σ) × √horizon` where `z = norm.ppf(1 − confidence)`.
     Return as a **positive** number.

---

## 7. CVaR / Expected Shortfall

File: `src/qis_risk_report/risk/metrics.py`

7.1  `expected_shortfall(returns: pd.Series, confidence: float = 0.99) -> float`
     Mean of returns that fall at or below the `(1 − confidence)` quantile.
     Return as a **positive** number (loss magnitude).

---

## 8. Correlation matrix

File: `src/qis_risk_report/risk/metrics.py`

8.1  `correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame`
     Pearson correlation across all columns.  Wrapper around `df.corr()`.

---

## 9. Test fixtures

Directory: `tests/fixtures/`

9.1  Create `returns_5d_simple.csv` — 5-row toy returns DataFrame with 4
     subcomponent columns + `total`.  Values chosen so all expected outputs can
     be hand-calculated.

9.2  Create `returns_20d.csv` — 20-row fixture for drawdown-duration and
     rolling-window tests (minimum meaningful length for a 21-day window).

9.3  Document expected outputs as inline comments in the test file (not in
     the CSV), so the fixture stays machine-readable.

---

## 10. Unit tests

File: `tests/test_metrics.py`

One test function per metric.  Each test:
- loads the relevant fixture via `pd.read_csv`
- calls the metric function
- asserts the result equals the hand-calculated expected value
  (use `pytest.approx` for floats)

Tests to cover:
- `cumulative_return` — geometric compounding verified on 5-row fixture
- `annualised_return` — scalar, verified against formula
- `annualised_volatility` — scalar (full) and rolling (window=21, using 20-row fixture)
- `sharpe_ratio` — zero risk-free and non-zero risk-free
- `sortino_ratio` — downside-only denominator
- `max_drawdown` — known peak and trough
- `drawdown_series` — shape and monotonicity check
- `drawdown_duration` — counted in calendar days
- `historical_var` at 99 % and 95 %, horizon 1 and 10
- `parametric_var` at 99 % and 95 %, horizon 1 and 10
- `expected_shortfall` at 99 % and 95 %
- `correlation_matrix` — shape, diagonal all 1.0, symmetry
