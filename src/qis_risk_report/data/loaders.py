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
    """Load daily returns for the broader portfolio instruments plus qis_total."""
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    if "qis_total" not in df.columns:
        raise ValueError(f"{path}: missing required column 'qis_total'")
    return df


def load_weights(path: str) -> pd.DataFrame:
    """Load portfolio weights per instrument over time. Rows must sum to 1.0."""
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    _validate_weights(df)
    return df


def _validate_returns(df: pd.DataFrame) -> None:
    if "total" not in df.columns:
        raise ValueError("returns_df: missing required column 'total'")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("returns_df: index must be a DatetimeIndex")


def _validate_weights(df: pd.DataFrame) -> None:
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("weights_df: index must be a DatetimeIndex")
    row_sums = df.sum(axis=1)
    if not (row_sums.sub(1.0).abs() < 1e-6).all():
        raise ValueError("weights_df: rows must sum to 1.0")
