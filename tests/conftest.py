import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def sample_returns() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2023-01-01", periods=252)
    return pd.DataFrame(
        rng.normal(0.0005, 0.01, size=(252, 3)),
        index=dates,
        columns=["StrategyA", "StrategyB", "StrategyC"],
    )
