"""Refresh BBG (if opened o/n): reload market-dependent datasets for the new day.

Reloads ONLY the market-sensitive data (inflation swaps, EUR linkers/bonds, EUR
close, related KDB files), recomputes Trade/Value dates, and detects an overnight
date rollover. Every file/UNC access goes through CurrentUserImpersonate.

`run(provider)` returns a clean action result (no Streamlit, reusable by pricers);
`render(provider)` runs it and draws the small result tables. No st.session_state:
the only persisted state (rollover marker) is a file.
"""

import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from instance import bql_bonds, config, exports
from instance.impersonation import CurrentUserImpersonate

_MARKER = ".last_refresh"


# --------------------------------------------------------------------------- #
# Dates
# --------------------------------------------------------------------------- #
def _now() -> dt.datetime:
    return dt.datetime.now(ZoneInfo(config.TIMEZONE))


def _stamp(now: dt.datetime) -> str:
    return now.strftime("%a %d-%m-%Y %H:%M:%S")


def _prev_business_day(d: dt.date) -> dt.date:
    d -= dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d


def _next_business_day(d: dt.date) -> dt.date:
    d += dt.timedelta(days=1)
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    return d


def _add_business_days(d: dt.date, n: int) -> dt.date:
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def _trade_value_dates(today: dt.date) -> pd.DataFrame:
    """Trade/Value date matrix (T+2). TODO(desk): plug holiday calendars per region."""
    trades = {
        "Yesterday": _prev_business_day(today),
        "Today": today,
        "Tomorrow": _next_business_day(today),
    }
    rows = [
        {
            "When": label,
            "Trade Date": trade.strftime("%d/%m/%Y"),
            "Value Date": _add_business_days(trade, 2).strftime("%d/%m/%Y"),
        }
        for label, trade in trades.items()
    ]
    return pd.DataFrame(rows)


def _detect_rollover(today: dt.date) -> bool:
    """Read + refresh the last-refresh marker. True when the date rolled over o/n."""
    marker = exports.resolved_dir() / _MARKER
    stored = None
    with CurrentUserImpersonate():
        try:
            stored = marker.read_text(encoding="utf-8").strip()
        except OSError:
            stored = None
    rollover = stored is not None and stored < today.isoformat()
    with CurrentUserImpersonate():
        try:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(today.isoformat(), encoding="utf-8")
        except OSError:
            pass
    return rollover


# --------------------------------------------------------------------------- #
# Dataset reloads
# --------------------------------------------------------------------------- #
def _row(dataset, status, source_path, rows, message, ts) -> dict:
    return {
        "dataset": dataset,
        "status": status,
        "source_path": source_path,
        "rows": rows,
        "message": message,
        "timestamp": ts,
    }


def _reload_market(provider, ts: str) -> list:
    """INF_SWAPS from Bloomberg; linker/nominal universes rebuilt via BQL.

    Mirrors the workbook's "Refresh BBG": re-pull the inflation-linked and
    nominal bond names from Bloomberg (BQL), falling back to the static config
    universe when the terminal is unavailable.
    """
    results = []

    swaps = provider.get_snapshot(config.INFLATION_SWAP_TICKERS, ["PX_LAST"])
    if not swaps.empty:
        results.append(_row("INF_SWAPS", "reloaded", "Bloomberg (EUSWI* Curncy)",
                            len(swaps), "Reloaded from Bloomberg", ts))
    else:
        results.append(_row("INF_SWAPS", "unavailable", "Bloomberg (EUSWI* Curncy)",
                            0, provider.message, ts))

    linkers, lk_src = bql_bonds.load_linkers(provider)
    results.append(_row(
        "EUR_LINKERS",
        "reloaded" if lk_src.startswith("Bloomberg") else "fallback",
        lk_src, len(linkers),
        "Rebuilt linker names via BQL" if lk_src.startswith("Bloomberg")
        else "BQL unavailable — static config universe", ts))

    bonds, nm_src = bql_bonds.load_nominals(provider)
    results.append(_row(
        "EUR_BONDS",
        "reloaded" if nm_src.startswith("Bloomberg") else "fallback",
        nm_src, len(bonds),
        "Rebuilt nominal names via BQL" if nm_src.startswith("Bloomberg")
        else "BQL unavailable — static config universe", ts))
    return results


def _reload_close_and_kdb(ts: str) -> list:
    """EUR_CLOSE + related KDB files from the UNC share (via impersonation)."""
    results = []
    kdb_dir = config.KDB_DIR.strip()

    for dataset, filename in config.KDB_FILES.items():
        if not kdb_dir:
            results.append(_row(dataset, "skipped", "(set [paths].kdb_dir)", 0,
                                "KDB path not configured", ts))
            continue
        path = f"{kdb_dir.rstrip(chr(92))}\\{filename}"
        with CurrentUserImpersonate():
            try:
                df = pd.read_csv(path)
                results.append(_row(dataset, "reloaded", path, len(df),
                                    "Reloaded from KDB share", ts))
            except Exception as exc:  # missing share / no access / bad file
                results.append(_row(dataset, "unavailable", path, 0,
                                    f"Read failed: {exc}", ts))
    return results


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def run(provider) -> dict:
    """Reload market datasets, recompute dates, detect rollover. Pure (no UI)."""
    now = _now()
    ts = _stamp(now)
    today = now.date()

    results = _reload_market(provider, ts) + _reload_close_and_kdb(ts)
    dates = _trade_value_dates(today)
    rollover = _detect_rollover(today)
    banner = (
        "Date rollover detected: market datasets reloaded"
        if rollover
        else "Manual market refresh completed"
    )
    return {
        "results": results,
        "dates": dates,
        "rollover": rollover,
        "banner": banner,
        "timestamp": ts,
    }


def render(provider) -> None:
    """Run the refresh and draw the small result tables under the workflow."""
    out = run(provider)

    if out["rollover"]:
        st.warning("🔁 " + out["banner"])
    else:
        st.success("✅ " + out["banner"])
    st.caption("Refresh timestamp: " + out["timestamp"])

    st.markdown("**Trade / Value dates**")
    st.dataframe(out["dates"], hide_index=True, width="stretch")

    st.markdown("**Refresh result**")
    st.dataframe(pd.DataFrame(out["results"]), hide_index=True, width="stretch")
