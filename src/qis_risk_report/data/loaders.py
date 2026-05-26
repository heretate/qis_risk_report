import os

import pandas as pd


def load_returns(path: str) -> pd.DataFrame:
    """Load daily returns for each QIS subcomponent and the aggregate strategy.

    Expected columns: <subcomponent> × 4, total
    Index: DatetimeIndex, business-day frequency, tz-naive
    """
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    _validate_returns(df)
    return df


def load_portfolio(path: str) -> pd.DataFrame:
    """Load daily returns for the broader portfolio instruments plus qis_total.

    Portfolio data starts from 2020; do not attempt to back-fill before that date.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"portfolio_returns file not found: {path}")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f"{path}: index must be a DatetimeIndex")
    if "qis_total" not in df.columns:
        raise ValueError(f"{path}: missing required column 'qis_total'")
    return df


def load_weights(path: str) -> pd.DataFrame:
    """Load portfolio weights per instrument over time. Rows must sum to 1.0."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"weights file not found: {path}")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    _validate_weights(df)
    return df


def common_date_range(
    qis_return_df: pd.DataFrame,
    portfolio_return_df: pd.DataFrame,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return the overlapping (start, end) date range between the two DataFrames."""
    start = max(qis_return_df.index[0], portfolio_return_df.index[0])
    end = min(qis_return_df.index[-1], portfolio_return_df.index[-1])
    return start, end


def load_factors(path: str) -> pd.DataFrame:
    """Load factor returns for attribution analysis.

    Expected columns: carry, momentum, value, volatility
    Index: DatetimeIndex, same date range as qis_return_df, tz-naive
    """
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    _validate_factors(df)
    return df


def _validate_factors(df: pd.DataFrame) -> None:
    required = {"carry", "momentum", "value", "volatility"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"factors_df: missing columns {missing}")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("factors_df: index must be a DatetimeIndex")


def _validate_returns(df: pd.DataFrame) -> None:
    if "total" not in df.columns:
        raise ValueError("qis_return_df: missing required column 'total'")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("qis_return_df: index must be a DatetimeIndex")


def _validate_weights(df: pd.DataFrame) -> None:
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("weights_df: index must be a DatetimeIndex")
    if "qis_total" not in df.columns:
        raise ValueError("weights_df: missing required column 'qis_total'")
    row_sums = df.sum(axis=1)
    if not (row_sums.sub(1.0).abs() < 1e-6).all():
        raise ValueError("weights_df: rows must sum to 1.0")
