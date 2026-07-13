"""Tab: Params — mirrors the Excel "Params" sheet (feeds, seaso, correspondence)."""

import pandas as pd
import streamlit as st

from instance import config


def render(provider) -> None:
    st.subheader("Params")

    if provider.is_available():
        st.success(f"Bloomberg: {provider.message}")
    else:
        st.warning(f"Bloomberg: {provider.message}")

    p = config.PARAMS
    c1, c2 = st.columns(2)
    with c1:
        feeds = pd.DataFrame(
            {
                "setting": [
                    "Reuters enabled",
                    "Bro feed available",
                    "Fixings bro feed available",
                    "Source",
                ],
                "value": [
                    p["reuters_enabled"],
                    p["bro_feed_available"],
                    p["fixings_bro_feed_available"],
                    p["source"],
                ],
            }
        )
        st.dataframe(feeds.astype(str), hide_index=True, width="stretch")
    with c2:
        calc = pd.DataFrame(
            {
                "setting": [
                    "Roll market",
                    "Seaso",
                    "Seaso calc type",
                    "ESTR fixing",
                    "Start histo date",
                ],
                "value": [
                    p["roll_market"] or "-",
                    p["seaso"],
                    p["seaso_calc_type"],
                    p["estr_fixing"],
                    p["start_histo_date"],
                ],
            }
        )
        st.dataframe(calc.astype(str), hide_index=True, width="stretch")

    st.caption(
        "MVP: only Bloomberg is wired. Reuters / broker feeds and KDB paths are "
        "shown for parity with the Excel and come later."
    )

    st.markdown("**Linker ↔ Nominal correspondence** (edit in `instance/config.py`):")
    st.dataframe(
        pd.DataFrame(config.correspondence()),
        hide_index=True,
        width="stretch",
    )

    # TODO(workspace): source feed flags, ESTR fixing and histo paths from
    # Workspace / KDB once those providers exist.
