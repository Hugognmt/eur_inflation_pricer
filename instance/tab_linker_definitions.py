"""Tab: BondDef_Infla — EUR inflation-linked bond definitions."""

import pandas as pd
import streamlit as st

from instance import config


def render(provider) -> None:
    st.subheader("BondDef_Infla")
    st.caption("EUR inflation-linked bond definitions (OAT€i / OATi / Bund€i / BTP€i).")

    st.dataframe(
        pd.DataFrame(config.linker_bonds()),
        hide_index=True,
        width="stretch",
    )

    if not provider.is_available():
        st.info(provider.message)

    # TODO: map desk labels to Bloomberg tickers/ISINs to pull live ref data.
    # TODO(workspace): enrich definitions from Workspace historical later.
