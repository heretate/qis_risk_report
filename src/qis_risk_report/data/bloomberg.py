"""Bloomberg data client.

Requires blpapi (pip install qis-risk-report[bloomberg]) and a running
Bloomberg Terminal or B-PIPE session on localhost:8194.
"""

from __future__ import annotations

import pandas as pd


class BloombergClient:
    """Thin wrapper around blpapi for fetching reference and historical data."""

    def __init__(self, host: str = "localhost", port: int = 8194) -> None:
        self.host = host
        self.port = port
        self._session: object = None

    def connect(self) -> None:
        try:
            import blpapi  # type: ignore[import]
        except ImportError as e:
            raise ImportError(
                "blpapi is not installed. Run: pip install 'qis-risk-report[bloomberg]'"
            ) from e

        options = blpapi.SessionOptions()
        options.setServerHost(self.host)
        options.setServerPort(self.port)
        self._session = blpapi.Session(options)
        if not self._session.start():
            raise RuntimeError("Failed to start Bloomberg session.")

    def disconnect(self) -> None:
        if self._session is not None:
            self._session.stop()

    def get_reference_data(
        self, securities: list[str], fields: list[str]
    ) -> pd.DataFrame:
        """Fetch current reference data (BDP equivalent)."""
        raise NotImplementedError

    def get_historical_data(
        self,
        securities: list[str],
        fields: list[str],
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """Fetch historical daily data (BDH equivalent)."""
        raise NotImplementedError

    def __enter__(self) -> "BloombergClient":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.disconnect()
