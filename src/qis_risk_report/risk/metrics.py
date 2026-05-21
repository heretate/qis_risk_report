"""Phase 1 — core risk-return metrics."""
import numpy as np
import pandas as pd
from scipy.stats import norm

TRADING_DAYS = 252


def cumulative_return(returns: pd.Series) -> pd.Series:
    return (1 + returns).cumprod() - 1


def annualised_return(returns: pd.Series) -> float:
    n = len(returns)
    total = float((1 + returns).prod())
    return float(total ** (TRADING_DAYS / n) - 1)


def annualised_volatility(returns: pd.Series, window: int | None = None) -> float | pd.Series:
    if window is None:
        return float(returns.std() * np.sqrt(TRADING_DAYS))
    return returns.rolling(window).std() * np.sqrt(TRADING_DAYS)


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    return (annualised_return(returns) - risk_free) / annualised_volatility(returns)


def sortino_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    daily_rf = risk_free / TRADING_DAYS
    downside = returns[returns < daily_rf]
    downside_vol = float(downside.std() * np.sqrt(TRADING_DAYS))
    return (annualised_return(returns) - risk_free) / downside_vol


def drawdown_series(returns: pd.Series) -> pd.Series:
    wealth = (1 + returns).cumprod()
    running_max = wealth.cummax()
    return wealth / running_max - 1


def max_drawdown(returns: pd.Series) -> float:
    return float(drawdown_series(returns).min())


def drawdown_duration(returns: pd.Series) -> int:
    wealth = (1 + returns).cumprod()
    running_max = wealth.cummax()
    below_peak = (wealth < running_max).values
    idx = returns.index
    n = len(below_peak)
    max_days = 0
    i = 0
    while i < n:
        if below_peak[i]:
            peak_i = i - 1  # day 0 can never be below its own cummax
            j = i
            while j < n and below_peak[j]:
                j += 1
            end_i = j - 1
            days = (idx[end_i] - idx[peak_i]).days
            max_days = max(max_days, days)
            i = j
        else:
            i += 1
    return max_days


def historical_var(returns: pd.Series, confidence: float = 0.99, horizon: int = 1) -> float:
    var = -returns.quantile(1 - confidence)
    return float(var * np.sqrt(horizon))


def parametric_var(returns: pd.Series, confidence: float = 0.99, horizon: int = 1) -> float:
    mu = returns.mean()
    sigma = returns.std()
    z = norm.ppf(1 - confidence)  # negative (left-tail z-score)
    return float(-(mu + z * sigma) * np.sqrt(horizon))


def expected_shortfall(returns: pd.Series, confidence: float = 0.99) -> float:
    threshold = returns.quantile(1 - confidence)
    tail = returns[returns <= threshold]
    return float(-tail.mean())


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.corr()
