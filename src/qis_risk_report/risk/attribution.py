"""Phase 2 — factor attribution and return decomposition."""
from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_ols_attribution(
    returns: pd.Series,
    factors: pd.DataFrame,
    window: int = 60,
) -> pd.DataFrame:
    """Rolling OLS regression of returns on factors.

    Returns a DataFrame with one column per factor (rolling betas) plus
    'r_squared'. Rows before the first full window are NaN.
    """
    factor_cols = list(factors.columns)
    out_cols = factor_cols + ["r_squared"]
    result = pd.DataFrame(np.nan, index=returns.index, columns=out_cols, dtype=float)

    aligned_returns = returns.reindex(factors.index)
    F = factors.values  # shape (n, k)
    y_all = aligned_returns.values  # shape (n,)

    for i in range(window - 1, len(y_all)):
        y = y_all[i - window + 1 : i + 1]
        X = F[i - window + 1 : i + 1]
        if np.isnan(y).any():
            continue
        X_const = np.column_stack([np.ones(window), X])
        betas, _, _, _ = np.linalg.lstsq(X_const, y, rcond=None)
        y_hat = X_const @ betas
        ss_res = float(((y - y_hat) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        r_sq = 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else 0.0
        for j, col in enumerate(factor_cols):
            result.iat[i, j] = betas[j + 1]
        result.iat[i, len(factor_cols)] = r_sq

    return result


def attribute_all(
    qis_return_df: pd.DataFrame,
    factors_df: pd.DataFrame,
    window: int = 60,
) -> dict[str, pd.DataFrame]:
    """Apply rolling OLS attribution to every column in qis_return_df."""
    return {
        col: rolling_ols_attribution(qis_return_df[col], factors_df, window=window)
        for col in qis_return_df.columns
    }


def contribution_decomposition(
    qis_return_df: pd.DataFrame,
    weights: pd.Series | None = None,
) -> pd.DataFrame:
    """Compute each subcomponent's contribution to total return per date.

    Contribution = return × weight. The 'total' column is the weighted sum.
    Accepts an optional weights Series (must sum to 1); defaults to equal
    weights across all non-'total' columns.
    """
    sub_cols = [c for c in qis_return_df.columns if c != "total"]
    if weights is None:
        w = pd.Series(1.0 / len(sub_cols), index=sub_cols)
    else:
        w = weights.reindex(sub_cols)

    contrib = qis_return_df[sub_cols].multiply(w, axis="columns")
    contrib["total"] = contrib.sum(axis=1)
    return contrib


def cumulative_contribution(
    qis_return_df: pd.DataFrame,
    weights: pd.Series | None = None,
) -> pd.DataFrame:
    """Cumulative contribution series alongside daily contributions."""
    daily = contribution_decomposition(qis_return_df, weights=weights)
    return daily.cumsum()
