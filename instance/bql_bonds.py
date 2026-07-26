"""Rebuild the bond universe from Bloomberg via BQL (the "Refresh BBG" step).

Runs the workbook's three BQL blocks through ``provider.get_bql`` to pull the
live linker and nominal bonds. The bond id and name come straight from the BQL
result (its ``id`` column is the security identifier/name; ``ID_ISIN`` the
ISIN) — nothing is synthesised here. When Bloomberg is unavailable (or a query
returns nothing), each loader falls back to the static ``config`` universe so
the tabs and pricers still have data.

Pure data layer — no Streamlit here; tabs/refresh render the returned frames.
"""

import pandas as pd

from instance import config

# Which BQL blocks make up each definition table.
LINKER_BLOCKS = ("linkers_reference_index", "linkers_series")
NOMINAL_BLOCKS = ("nominals",)


def run_blocks(provider, keys) -> list[dict]:
    """Run each BQL block once; return [{key, query, df}] with the raw output."""
    out = []
    for key in keys:
        query = config.build_bql_query(key)
        out.append({"key": key, "query": query, "df": provider.get_bql(query)})
    return out


def combine(blocks: list[dict], fallback_fn) -> tuple[pd.DataFrame, str]:
    """Concatenate the blocks' raw BQL output; fall back to static config."""
    frames = [b["df"] for b in blocks if not b["df"].empty]
    if frames:
        return pd.concat(frames, ignore_index=True), "Bloomberg (BQL)"
    return pd.DataFrame(fallback_fn()), "config (fallback)"


def load_linkers(provider) -> tuple[pd.DataFrame, str]:
    """Linkers = reference-index block + series block (BQL), else static config."""
    return combine(run_blocks(provider, LINKER_BLOCKS), config.linker_bonds)


def load_nominals(provider) -> tuple[pd.DataFrame, str]:
    """Nominal comparator universe (BQL), else static config."""
    return combine(run_blocks(provider, NOMINAL_BLOCKS), config.nominal_bonds)
