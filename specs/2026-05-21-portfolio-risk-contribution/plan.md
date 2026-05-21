# Phase 3 — Portfolio Risk Contribution: Plan

## Task Group 1 — Data Loaders

1. Add `portfolio_returns_path` and `weights_path` to `config/settings.yaml`.
2. Implement `load_portfolio(path: str) -> pd.DataFrame` in `src/qis_risk_report/data/loaders.py`. Must raise `FileNotFoundError` with a descriptive message if the path does not exist, and `ValueError` if `qis_total` column is absent or the index is not a `DatetimeIndex`.
3. Implement `load_weights(path: str) -> pd.DataFrame` in `loaders.py`. Must raise `FileNotFoundError` if the path does not exist, `ValueError` if `qis_total` is absent, and `ValueError` if any row sums to a value outside `[1.0 ± 1e-6]`.
4. Add `tests/fixtures/portfolio_returns.csv` and `tests/fixtures/weights.csv` — small synthetic DataFrames (5 instruments, 60 rows) for use across all Phase 3 tests.

## Task Group 2 — Marginal VaR and Component VaR

5. Implement `marginal_var(portfolio_returns: pd.DataFrame, weights: pd.Series, confidence: float = 0.95) -> pd.Series` in `src/qis_risk_report/risk/portfolio.py`. Uses parametric covariance: `ΔVAR_i = (Cov(r_i, r_P) / σ_P) × z × w_i`. Returns a Series indexed by instrument name.
6. Implement `component_var(portfolio_returns: pd.DataFrame, weights: pd.Series, confidence: float = 0.95) -> pd.Series` in `portfolio.py`. Formula: `CVaR_i = ρ(r_i, r_P) × standalone_VaR_i × w_i`. Component VaRs must sum to total portfolio VaR.
7. Expose `portfolio_var(portfolio_returns: pd.DataFrame, weights: pd.Series, confidence: float = 0.95) -> float` as a shared helper used by both functions above.
8. Write `tests/fixtures/marginal_var_expected.csv` and `tests/fixtures/component_var_expected.csv` — pre-computed from the synthetic fixtures using an independent hand-calculation (e.g. a throwaway notebook or spreadsheet).

## Task Group 3 — Correlation and Diversification Benefit

9. Implement `qis_portfolio_correlation(returns_df: pd.DataFrame, portfolio_returns: pd.DataFrame) -> pd.Series` in `portfolio.py`. Returns Pearson correlation of each QIS subcomponent (and `total`) with the `portfolio_returns` aggregate (i.e. `portfolio_returns @ weights`). The function accepts a `weights` argument for the portfolio aggregate; defaults to equal weight if omitted.
10. Implement `diversification_benefit(portfolio_returns: pd.DataFrame, weights: pd.Series, confidence: float = 0.95) -> float` in `portfolio.py`. Computes `Σ(w_i × standalone_VaR_i) − portfolio_VaR`. Result is non-negative by construction; raise `ValueError` if negative (indicates a bug in the caller's inputs).
11. Write `tests/fixtures/portfolio_correlation_expected.csv` — Pearson correlations pre-computed from the synthetic fixture.

## Task Group 4 — Unit Tests

12. Write `tests/test_portfolio.py` covering:
    - `load_portfolio` and `load_weights`: happy path, missing file, missing column, invalid row sums (weights).
    - `marginal_var`: known-input fixture → values match `marginal_var_expected.csv` within `1e-6`; values sum to `portfolio_var` within `1e-8`.
    - `component_var`: known-input fixture → values match `component_var_expected.csv` within `1e-6`; values sum to `portfolio_var` within `1e-8`.
    - `qis_portfolio_correlation`: fixture → values match `portfolio_correlation_expected.csv` within `1e-6`; all values in `[-1, 1]`.
    - `diversification_benefit`: fixture → scalar result is non-negative; equals `Σ(w_i × standalone_VaR_i) − portfolio_var` within `1e-8`.
    - `diversification_benefit`: raises `ValueError` on degenerate inputs that produce a negative result.
