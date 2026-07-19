"""Static configuration for the EUR inflation desk MVP.

Mirrors the Excel workbook (WF_ExportDatas) it replaces:
- the "Params" sheet -> PARAMS + the linker/nominal correspondence table
- CPI / inflation-swap Bloomberg tickers used by the live tabs

Everything here is meant to be hand-edited by the desk.
"""

import re
import tomllib
from pathlib import Path

_SETTINGS_PATH = Path(__file__).with_name("settings.toml")


def _load_settings() -> dict:
    try:
        with open(_SETTINGS_PATH, "rb") as f:
            return tomllib.load(f)
    except Exception:
        # Missing/broken settings should not stop the app from starting.
        return {}


SETTINGS = _load_settings()

APP_TITLE = SETTINGS.get("app", {}).get("title", "EUR Inflation Desk")
TIMEZONE = SETTINGS.get("app", {}).get("timezone", "Europe/Paris")
DEFAULT_LOOKBACK_DAYS = int(SETTINGS.get("data", {}).get("default_lookback_days", 30))

# Where loaded data is saved as CSV for the pricers, and the target file names
# (mirrors the Excel "DatasToImport" paths). dataset key -> CSV file name.
EXPORT_DIR = SETTINGS.get("export", {}).get("dir", "exports")
EXPORT_FILES = {
    "BondDefInfla": "BondDefInfla.csv",
    "BondDefNominals": "BondDefNominals.csv",
    "CpiMatrix": "CpiMatrix.csv",
    "InfSwaps": "InfSwaps.csv",
    "EurLinkers": "EurLinkers.csv",
    "EurBonds": "EurBonds.csv",
}

# UNC share holding the KDB export/close files (Excel Params "Path" rows).
# Set in settings.toml [paths].kdb_dir; empty means "not configured".
KDB_DIR = SETTINGS.get("paths", {}).get("kdb_dir", "")
KDB_FILES = {
    "EUR_CLOSE_LINKERS": "KDBexportLastLinkersClose.csv",
    "EUR_CLOSE_BONDS": "KDBexportLastBondsClose.csv",
    "KDB_LINKERS": "KDBexportLastLinkers.csv",
    "KDB_BONDS": "KDBexportLastBonds.csv",
}

# ---------------------------------------------------------------------------
# Params sheet (mirrors the orange/blue config blocks in the Excel "Params").
# MVP wires Bloomberg only; the other feeds are shown for parity, wired later.
# ---------------------------------------------------------------------------
PARAMS = {
    "reuters_enabled": True,
    "bro_feed_available": True,
    "fixings_bro_feed_available": True,
    "source": "BROKER",            # TODO(workspace): BLOOMBERG for now in practice
    "roll_market": None,           # Excel showed #VALUE! -> unset
    "seaso": "Totem",
    "seaso_calc_type": "LCH",
    "estr_fixing": 1.926,
    "start_histo_date": "2026-01-06",
}

# Export sheet action steps (each stamps a "last run" time in the UI).
WORKFLOW_STEPS = [
    "1) Refresh BBG (if opened o/n)",
    "2) Initialise",
    "3) Export/Import KDB",
    "4) Import Close",
    "5) Export datas",
]

# Intraday dynamic-time export snapshots (Excel "Time" row).
SNAPSHOT_TIMES = ["14:30:00", "14:35:00"]

# ---------------------------------------------------------------------------
# Bond universe: linker -> matched nominal, straight from the "Params" sheet.
# Desk label format: <ISSUER>[e|i]_[G_]<Mon-YY>_<coupon>.  Editable.
# (List truncated to the legible rows; extend as needed.)
# ---------------------------------------------------------------------------
LINKER_NOMINAL_PAIRS = [
    ("OATe_Jul-27_1.85", "OAT_Oct-27_2.75"),
    ("OATe_Mar-29_0.1", "OAT_May-29_0.5"),
    ("OATe_Jul-30_0.7", "OAT_May-30_2.5"),
    ("OATe_Jul-31_0.1", "OAT_May-31_1.5"),
    ("OATe_Jul-32_3.15", "OAT_Oct-32_5.75"),
    ("OATe_Jul-34_0.6", "OAT_May-34_1.25"),
    ("OATe_Jul-36_0.1", "OAT_May-36_1.25"),
    ("OATe_G_Jul-38_0.1", "OAT_May-38_1.25"),
    ("OATe_Jul-40_1.8", "OAT_May-40_0.5"),
    ("OATe_Jul-43_0.95", "OAT_May-43_2.5"),
    ("OATe_Jul-47_0.1", "OAT_May-48_2"),
    ("OATe_Jul-53_0.1", "OAT_May-53_0.75"),
    ("OATi_Mar-28_0.1", "OAT_May-28_0.75"),
    ("OATi_Jul-29_3.4", "OAT_Apr-29_5.5"),
    ("OATi_Mar-32_0.1", "OAT_Nov-31_0"),
    ("OATi_Mar-36_0.1", "OAT_May-36_1.25"),
    ("OATi_Mar-39_0.55", "OAT_May-38_1.25"),
    ("BUNDe_Apr-30_0.5", "BUND_Feb-30_0"),
    ("BUNDe_Apr-33_0.1", "BUND_Feb-33_2.3"),
    ("BUNDe_Apr-46_0.1", "BUND_Aug-46_2.5"),
    ("BTPe_Sep-26_3.1", "BTP_Sep-26_3.85"),
    ("BTPe_May-28_1.3", "BTP_Sep-28_4.75"),
    ("BTPe_May-29_1.5", "BTP_Jun-29_2.8"),
    ("BTPe_May-30_0.4", "BTP_Apr-30_1.35"),
]

# CPI / HICP reference indices (Bloomberg). Editable placeholders.
CPI_TICKERS = [
    "CPTFEMU Index",   # Euro area HICP ex-tobacco (linker reference)
    "FRCPXTOB Index",  # France CPI ex-tobacco
    "CPALEMU Index",   # Euro area HICP all items
]

# EUR zero-coupon inflation swaps (HICPxT). Editable placeholders.
INFLATION_SWAP_TICKERS = [
    "EUSWI1 Curncy",
    "EUSWI2 Curncy",
    "EUSWI5 Curncy",
    "EUSWI10 Curncy",
    "EUSWI30 Curncy",
]

# ---------------------------------------------------------------------------
# Helpers to turn desk labels into structured bond definitions.
# ---------------------------------------------------------------------------
_ISSUERS = {"OAT": "France", "BUND": "Germany", "BTP": "Italy"}


def parse_bond(label: str) -> dict:
    """'OATe_Jul-27_1.85' -> {label, issuer, type, maturity, coupon}."""
    parts = label.split("_")
    prefix = parts[0]
    coupon = float(parts[-1])
    mon, yy = next(p for p in parts if "-" in p).split("-")
    root = re.match(r"[A-Z]+", prefix).group(0)   # OAT / BUND / BTP
    return {
        "label": label,
        "issuer": _ISSUERS.get(root, root),
        "type": "Linker" if prefix != root else "Nominal",
        "maturity": f"{mon}-20{yy}",
        "coupon": coupon,
    }


def linker_bonds() -> list[dict]:
    return [parse_bond(linker) for linker, _ in LINKER_NOMINAL_PAIRS]


def nominal_bonds() -> list[dict]:
    seen, out = set(), []
    for _, nominal in LINKER_NOMINAL_PAIRS:
        if nominal not in seen:
            seen.add(nominal)
            out.append(parse_bond(nominal))
    return out


def correspondence() -> list[dict]:
    return [{"Linker": lk, "Nominal corresp": nm} for lk, nm in LINKER_NOMINAL_PAIRS]
