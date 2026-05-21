"""Phase 3 — portfolio risk contribution metrics."""
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
    returns_df: pd.DataFrame,
    portfolio_returns: pd.DataFrame,
    weights: pd.Series | None = None,
) -> pd.Series:
    """Pearson correlation of each column in returns_df with the portfolio aggregate.

    The aggregate is portfolio_returns @ weights (equal-weight if weights is None).
    """
    if weights is None:
        n = len(portfolio_returns.columns)
        w = pd.Series(1.0 / n, index=portfolio_returns.columns)
    else:
        w = weights.reindex(portfolio_returns.columns)
    r_agg = portfolio_returns @ w
    result = returns_df.corrwith(r_agg)
    result.name = "correlation"
    return result


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
