"""CSV and Excel data loaders."""

from pathlib import Path
import pandas as pd


def load_csv(path: str | Path, **kwargs: object) -> pd.DataFrame:
    return pd.read_csv(path, **kwargs)


def load_excel(path: str | Path, sheet_name: str | int = 0, **kwargs: object) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl", **kwargs)
