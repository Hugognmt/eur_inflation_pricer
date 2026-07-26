"""Thin Bloomberg data provider built on xbbg.

Kept deliberately compact. Availability = xbbg importable AND a terminal API
session reachable (fast socket probe on 127.0.0.1:8194). When unavailable,
every call returns an empty DataFrame and `.message` explains why, so the UI
never blocks on a ~20s blpapi handshake and never crashes.

TODO(workspace): mirror this interface with WorkspaceLiveProvider /
WorkspaceHistoryProvider later so tabs can stay provider-agnostic.
"""

import socket

import pandas as pd

try:
    from xbbg import blp
    _XBBG_AVAILABLE = True
    # Pin the pandas backend: this xbbg build defaults to pyarrow, which here
    # demands pyarrow >= 22 (only 21 is installed) and fails every call. We
    # return pandas DataFrames anyway, so pandas is the right backend.
    try:
        blp.set_backend("pandas")
    except Exception:
        pass
except Exception:  # xbbg missing or import-time failure
    blp = None
    _XBBG_AVAILABLE = False

# Bloomberg Desktop/Server API default endpoint.
_BBG_HOST = "127.0.0.1"
_BBG_PORT = 8194


class BloombergProvider:
    def __init__(self) -> None:
        self.recheck()

    def recheck(self) -> bool:
        """(Re-)probe the terminal and refresh availability + message.

        Called at construction and whenever the UI asks to reconnect, so a
        terminal that comes up after the app started is picked up without a
        full server restart.
        """
        self._available = _XBBG_AVAILABLE and self._probe()
        if not _XBBG_AVAILABLE:
            self.message = "Bloomberg unavailable: xbbg not installed."
        elif not self._available:
            self.message = (
                f"Bloomberg unavailable: no terminal session on "
                f"{_BBG_HOST}:{_BBG_PORT}."
            )
        else:
            self.message = "Bloomberg (xbbg) connected."
        return self._available

    @staticmethod
    def _probe() -> bool:
        """Fast check that a Bloomberg terminal API session is listening."""
        try:
            with socket.create_connection((_BBG_HOST, _BBG_PORT), timeout=1.0):
                return True
        except OSError:
            return False

    def is_available(self) -> bool:
        return self._available

    def get_snapshot(self, tickers, fields) -> pd.DataFrame:
        """Reference/snapshot data (bdp). One row per ticker."""
        if not self._available or not tickers:
            return pd.DataFrame()
        try:
            return blp.bdp(tickers=tickers, flds=fields)
        except Exception as exc:
            self.message = f"Bloomberg snapshot failed: {exc}"
            return pd.DataFrame()

    def get_bql(self, expression) -> pd.DataFrame:
        """Run a Bloomberg Query Language (BQL) expression.

        Used to rebuild the bond universe (the workbook's "Refresh BBG" step):
        one row per security, columns ``id`` + one per requested field. Returns
        an empty DataFrame when Bloomberg is unavailable or the query fails, so
        callers can fall back to the static config universe.
        """
        if not self._available or not expression:
            return pd.DataFrame()
        try:
            result = blp.bql(expression)
            # xbbg's bql return type is loosely typed (Any); it is a pandas
            # DataFrame at runtime, but normalise defensively either way.
            if isinstance(result, pd.DataFrame):
                return result
            return pd.DataFrame(result)
        except Exception as exc:
            self.message = f"Bloomberg BQL failed: {exc}"
            return pd.DataFrame()

    def get_history(self, tickers, field, start_date, end_date) -> pd.DataFrame:
        """Historical time series (bdh) for a single field across tickers."""
        if not self._available or not tickers:
            return pd.DataFrame()
        try:
            return blp.bdh(
                tickers=tickers,
                flds=field,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            self.message = f"Bloomberg history failed: {exc}"
            return pd.DataFrame()
