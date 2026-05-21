"""Phase 1 — core risk-return metrics."""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def annualised_return(returns: pd.Series) -> float:
    raise NotImplementedError


def annualised_volatility(returns: pd.Series, window: int | None = None) -> float | pd.Series:
    raise NotImplementedError


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    raise NotImplementedError


def sortino_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    raise NotImplementedError


def max_drawdown(returns: pd.Series) -> float:
    raise NotImplementedError


def drawdown_duration(returns: pd.Series) -> int:
    raise NotImplementedError


def historical_var(returns: pd.Series, confidence: float = 0.99, horizon: int = 1) -> float:
    raise NotImplementedError


def parametric_var(returns: pd.Series, confidence: float = 0.99, horizon: int = 1) -> float:
    raise NotImplementedError


def expected_shortfall(returns: pd.Series, confidence: float = 0.99) -> float:
    raise NotImplementedError


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError
