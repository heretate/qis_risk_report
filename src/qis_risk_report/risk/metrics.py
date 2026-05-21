"""Standard QIS risk metrics computed from a returns series."""

from __future__ import annotations

import numpy as np
import pandas as pd


class RiskMetrics:
    """Compute risk metrics from a daily returns DataFrame (assets as columns)."""

    def __init__(self, returns: pd.DataFrame, periods_per_year: int = 252) -> None:
        self.returns = returns
        self.periods_per_year = periods_per_year

    def annualized_return(self) -> pd.Series:
        n = len(self.returns)
        return (1 + self.returns).prod() ** (self.periods_per_year / n) - 1

    def annualized_volatility(self) -> pd.Series:
        return self.returns.std() * np.sqrt(self.periods_per_year)

    def sharpe_ratio(self, risk_free_rate: float = 0.0) -> pd.Series:
        excess = self.annualized_return() - risk_free_rate
        vol = self.annualized_volatility()
        return excess / vol

    def max_drawdown(self) -> pd.Series:
        cum = (1 + self.returns).cumprod()
        rolling_max = cum.cummax()
        drawdown = (cum - rolling_max) / rolling_max
        return drawdown.min()

    def value_at_risk(self, confidence: float = 0.95) -> pd.Series:
        return self.returns.quantile(1 - confidence)

    def summary(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Ann. Return": self.annualized_return(),
                "Ann. Volatility": self.annualized_volatility(),
                "Sharpe Ratio": self.sharpe_ratio(),
                "Max Drawdown": self.max_drawdown(),
                "VaR (95%)": self.value_at_risk(),
            }
        )
