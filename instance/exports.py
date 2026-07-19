"""CSV export references + helpers.

Mirrors the Excel "Params / DatasToImport" paths: the data loaded in the app is
written to CSV files that downstream pricers (notably the linker pricer) read as
input. One function collects the current datasets, one writes them all out.
"""

from pathlib import Path

import pandas as pd

from instance import config
from instance.impersonation import CurrentUserImpersonate

_ROOT = Path(__file__).resolve().parent.parent


def resolved_dir() -> Path:
    """Export folder: absolute as-is, else relative to the project root."""
    d = Path(config.EXPORT_DIR)
    return d if d.is_absolute() else _ROOT / d


def _csv_index(df: pd.DataFrame) -> bool:
    """Keep the index for Bloomberg snapshots (ticker index), drop it otherwise."""
    return not isinstance(df.index, pd.RangeIndex)


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=_csv_index(df)).encode("utf-8")


def collect(provider) -> dict:
    """Build the datasets currently loadable in the app, keyed by export name.

    Bond definitions / monitors come from config; CPI and inflation swaps use
    Bloomberg when a session is available, else fall back to the ticker list so
    the target file still exists for the pricer.
    """
    data = {
        "BondDefInfla": pd.DataFrame(config.linker_bonds()),
        "BondDefNominals": pd.DataFrame(config.nominal_bonds()),
        "EurLinkers": pd.DataFrame(config.linker_bonds()),
        "EurBonds": pd.DataFrame(config.nominal_bonds()),
    }

    cpi = provider.get_snapshot(config.CPI_TICKERS, ["PX_LAST", "SECURITY_NAME"])
    data["CpiMatrix"] = cpi if not cpi.empty else pd.DataFrame({"ticker": config.CPI_TICKERS})

    swaps = provider.get_snapshot(config.INFLATION_SWAP_TICKERS, ["PX_LAST"])
    data["InfSwaps"] = swaps if not swaps.empty else pd.DataFrame(
        {"ticker": config.INFLATION_SWAP_TICKERS}
    )

    return data


def write_all(data: dict) -> list:
    """Write every dataset to its CSV target. Returns [(name, path, rows), ...]."""
    root = resolved_dir()
    written = []
    with CurrentUserImpersonate():
        root.mkdir(parents=True, exist_ok=True)
        for key, df in data.items():
            path = root / config.EXPORT_FILES[key]
            path.write_bytes(to_csv_bytes(df))
            written.append((key, path, len(df)))
    return written
