import pandas as pd
from qis_risk_report.risk import RiskMetrics


def test_summary_shape(sample_returns: pd.DataFrame) -> None:
    summary = RiskMetrics(sample_returns).summary()
    assert summary.shape == (3, 5)
    assert list(summary.columns) == [
        "Ann. Return", "Ann. Volatility", "Sharpe Ratio", "Max Drawdown", "VaR (95%)"
    ]


def test_max_drawdown_negative(sample_returns: pd.DataFrame) -> None:
    mdd = RiskMetrics(sample_returns).max_drawdown()
    assert (mdd <= 0).all()


def test_volatility_positive(sample_returns: pd.DataFrame) -> None:
    vol = RiskMetrics(sample_returns).annualized_volatility()
    assert (vol > 0).all()
