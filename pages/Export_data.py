"""EUR inflation desk - main Streamlit page (replaces the Excel "Export" sheet).

Top of page: connection status, Europe/Paris as-of, refresh, and the Excel's
5-step export workflow (each button stamps a last-run time). No sidebar.
Everything else lives in tabs mirroring the workbook's sheets. One
BloombergProvider is created once and passed to each tab's render(provider).

Run with:  streamlit run pages/Export_data.py
"""

import datetime as dt
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

# Make the project root importable so `from instance import ...` works whether
# this page is launched directly or as part of a wider multipage app later.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from instance import config  # noqa: E402
from instance.bloomberg import BloombergProvider  # noqa: E402
from instance import (  # noqa: E402
    tab_connection_params,
    tab_linker_definitions,
    tab_nominal_definitions,
    tab_cpi_fixings,
    tab_inflation_swaps,
    tab_eur_linkers_monitor,
    tab_eur_bonds_monitor,
    refresh,
)


@st.cache_resource
def get_provider() -> BloombergProvider:
    """One provider per server session (keeps any terminal session alive)."""
    return BloombergProvider()


def _now_str() -> str:
    now = dt.datetime.now(ZoneInfo(config.TIMEZONE))
    return now.strftime("%a %d-%m-%Y %H:%M:%S")


def _top_controls(provider) -> None:
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        if provider.is_available():
            st.success("Bloomberg: connected")
        else:
            st.error("Bloomberg: not available")
    with c2:
        st.metric("As of (Europe/Paris)", _now_str())
    with c3:
        st.write("")  # small vertical nudge to align the button
        if st.button("Refresh", width="stretch"):
            st.cache_data.clear()
            st.rerun()


def _workflow(provider) -> None:
    """The Excel "Export" sheet: 5 sequential steps, each stamping a run time."""
    st.markdown("**Export workflow**")
    # Same size for every step button, and a light-orange look.
    n = len(config.WORKFLOW_STEPS)
    sel = ",".join(f".st-key-step_{i} button" for i in range(n))
    sel_hover = ",".join(f".st-key-step_{i} button:hover" for i in range(n))
    st.markdown(
        f"<style>"
        f"{sel}{{height:4.5em;white-space:normal;"
        f"background-color:#FFD9A0;color:#7a4e00;border:1px solid #E8A44D;}}"
        f"{sel_hover}{{background-color:#FFC670;color:#5a3800;border-color:#D98B2B;}}"
        f"</style>",
        unsafe_allow_html=True,
    )
    # No st.session_state: a click renders its result inline in the same run.
    clicked = None
    cols = st.columns(len(config.WORKFLOW_STEPS))
    for i, (col, step) in enumerate(zip(cols, config.WORKFLOW_STEPS)):
        with col:
            if st.button(step, width="stretch", key=f"step_{i}"):
                clicked = i
    st.caption("Dynamic-time snapshots: " + " · ".join(config.SNAPSHOT_TIMES))

    if clicked == 0:
        # (1) Refresh BBG (if opened o/n): reload market datasets for the new day.
        refresh.render(provider)
    elif clicked is not None:
        st.info(f"{config.WORKFLOW_STEPS[clicked]} — not wired yet (MVP stub).")
    # TODO(workspace): wire steps 3-5 to KDB export/import and close import.


def main() -> None:
    st.set_page_config(page_title=config.APP_TITLE, layout="wide")
    st.title(config.APP_TITLE)

    provider = get_provider()
    _top_controls(provider)
    _workflow(provider)
    st.divider()

    tabs = st.tabs(
        [
            "Params",
            "BondDef_Infla",
            "BondDef_Nom",
            "CPI_Matrix",
            "INF_Swaps",
            "EUR_Linkers",
            "EUR_Bonds",
        ]
    )

    with tabs[0]:
        tab_connection_params.render(provider)
    with tabs[1]:
        tab_linker_definitions.render(provider)
    with tabs[2]:
        tab_nominal_definitions.render(provider)
    with tabs[3]:
        tab_cpi_fixings.render(provider)
    with tabs[4]:
        tab_inflation_swaps.render(provider)
    with tabs[5]:
        tab_eur_linkers_monitor.render(provider)
    with tabs[6]:
        tab_eur_bonds_monitor.render(provider)


main()
