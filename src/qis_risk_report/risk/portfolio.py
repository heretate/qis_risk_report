"""Phase 3 — portfolio risk contribution metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


def portfolio_var(
    portfolio_returns: pd.DataFrame,
    weights: pd.Series,
    confidence: float = 0.95,
) -> float:
    """Parametric portfolio VaR using the full covariance matrix.

    σ_P = sqrt(w^T Σ w); VaR = z × σ_P (expressed as a positive loss).
    """
    w = weights.reindex(portfolio_returns.columns).values
    sigma = portfolio_returns.cov().values
    sigma_p = float(np.sqrt(w @ sigma @ w))
    z = norm.ppf(confidence)
    return float(z * sigma_p)


def marginal_var(
    portfolio_returns: pd.DataFrame,
    weights: pd.Series,
    confidence: float = 0.95,
) -> pd.Series:
    """Weight-adjusted marginal VaR per instrument.

    ΔVAR_i = (Cov(r_i, r_P) / σ_P) × z × w_i
    Values sum to portfolio_var at the same confidence level.
    """
    w = weights.reindex(portfolio_returns.columns)
    cov = portfolio_returns.cov()
    r_p = portfolio_returns @ w
    sigma_p = float(r_p.std())
    z = norm.ppf(confidence)
    cov_with_port = cov @ w  # [Σ w]_i = Cov(r_i, r_P)
    result = (cov_with_port / sigma_p) * z * w
    result.name = "marginal_var"
    return result


def component_var(
    portfolio_returns: pd.DataFrame,
    weights: pd.Series,
    confidence: float = 0.95,
) -> pd.Series:
    """Component VaR per instrument using correlation decomposition.

    CVaR_i = ρ(r_i, r_P) × standalone_VaR_i × w_i
    Values sum to portfolio_var at the same confidence level.
    """
    w = weights.reindex(portfolio_returns.columns)
    r_p = portfolio_returns @ w
    sigma_p = float(r_p.std())
    z = norm.ppf(confidence)
    cov = portfolio_returns.cov()
    cov_with_port = cov @ w  # Cov(r_i, r_P)
    sigmas = portfolio_returns.std()
    rho = cov_with_port / (sigmas * sigma_p)  # ρ(r_i, r_P)
    standalone = z * sigmas
    result = rho * standalone * w
    result.name = "component_var"
    return result


def qis_portfolio_correlation(
    qis_return_df: pd.DataFrame,
    portfolio_returns: pd.DataFrame,
    weights: pd.Series | None = None,
) -> pd.Series:
    """Pearson correlation of each column in qis_return_df with the portfolio aggregate.

    The aggregate is portfolio_returns @ weights (equal-weight if weights is None).
    """
    if weights is None:
        n = len(portfolio_returns.columns)
        w = pd.Series(1.0 / n, index=portfolio_returns.columns)
    else:
        w = weights.reindex(portfolio_returns.columns)
    r_agg = portfolio_returns @ w
    result = qis_return_df.corrwith(r_agg)
    result.name = "correlation"
    return result


def compute_portfolio_contribution_at_weight(
    qis_return_df: pd.DataFrame,
    portfolio_return_df: pd.DataFrame,
    weights_df: pd.DataFrame,
    qis_weight: float,
    confidence: float = 0.95,
) -> dict:
    """Compute portfolio risk contribution metrics at a hypothetical QIS allocation.

    Builds a blended portfolio over the common date range (2020-onward overlap).
    Non-QIS instrument weights are scaled proportionally to sum to (1 - qis_weight).

    Returns dict with keys: standalone_var, marginal_var, component_var_share,
    correlation, diversification_benefit.
    """
    from qis_risk_report.data.loaders import common_date_range
    from qis_risk_report.risk.metrics import historical_var

    start, end = common_date_range(qis_return_df, portfolio_return_df)
    qis_slice = qis_return_df.loc[start:end, "total"]
    port_slice = portfolio_return_df.loc[start:end]

    non_qis_cols = [c for c in port_slice.columns if c != "qis_total"]
    last_w = weights_df.iloc[-1]
    non_qis_w = last_w.reindex(non_qis_cols).fillna(0)
    non_qis_total = float(non_qis_w.sum())
    if non_qis_total > 0:
        non_qis_w = non_qis_w * (1.0 - qis_weight) / non_qis_total

    blended_cols = non_qis_cols + ["qis_total"]
    blended_df = port_slice[blended_cols].copy()
    blended_df["qis_total"] = qis_slice.values
    blended_w = pd.concat([non_qis_w, pd.Series({"qis_total": qis_weight})])

    qis_standalone_var = historical_var(qis_slice, confidence=confidence)
    mv = marginal_var(blended_df, blended_w, confidence=confidence)
    qis_mv = float(mv.get("qis_total", float("nan")))
    cv = component_var(blended_df, blended_w, confidence=confidence)
    cv_total = float(cv.sum())
    qis_cv = float(cv.get("qis_total", float("nan")))
    qis_cv_share = qis_cv / cv_total if cv_total != 0 else float("nan")
    r_p = blended_df @ blended_w
    trailing_corr = float(qis_slice.corr(r_p))
    try:
        div_benefit = diversification_benefit(blended_df, blended_w, confidence=confidence)
    except ValueError:
        div_benefit = float("nan")

    return {
        "standalone_var": qis_standalone_var,
        "marginal_var": qis_mv,
        "component_var_share": qis_cv_share,
        "correlation": trailing_corr,
        "diversification_benefit": div_benefit,
    }


def build_portfolio_contribution_grid(
    qis_return_df: pd.DataFrame,
    portfolio_return_df: pd.DataFrame,
    weights_df: pd.DataFrame,
    weights_list: list[float],
    confidence: float = 0.95,
) -> pd.DataFrame:
    """Build a sensitivity grid of portfolio risk metrics across hypothetical QIS weights.

    Rows: each weight in weights_list (formatted as '1.0%' etc.).
    Columns: standalone_var, marginal_var, component_var_share, correlation,
             diversification_benefit.
    """
    rows = {}
    for w in weights_list:
        rows[f"{w:.1%}"] = compute_portfolio_contribution_at_weight(
            qis_return_df, portfolio_return_df, weights_df, w, confidence=confidence
        )
    return pd.DataFrame(rows).T


def diversification_benefit(
    portfolio_returns: pd.DataFrame,
    weights: pd.Series,
    confidence: float = 0.95,
) -> float:
    """Diversification benefit: Σ(w_i × standalone_VaR_i) − portfolio_VaR.

    Raises ValueError if the result is negative (indicates degenerate inputs).
    """
    w = weights.reindex(portfolio_returns.columns)
    z = norm.ppf(confidence)
    sigmas = portfolio_returns.std()
    standalone_sum = float((w * z * sigmas).sum())
    port_var = portfolio_var(portfolio_returns, weights, confidence)
    benefit = standalone_sum - port_var
    if benefit < 0:
        raise ValueError(
            f"diversification_benefit is negative ({benefit:.6g}), "
            "which indicates degenerate inputs (e.g. perfectly anti-correlated)."
        )
    return float(benefit)
