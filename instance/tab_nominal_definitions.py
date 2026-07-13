"""Tab: BondDef_Nom — EUR nominal bond definitions (matched to the linkers)."""

import pandas as pd
import streamlit as st

from instance import config


def render(provider) -> None:
    st.subheader("BondDef_Nom")
    st.caption("EUR nominal government bonds used as the linkers' nominal correspondence.")

    st.dataframe(
        pd.DataFrame(config.nominal_bonds()),
        hide_index=True,
        width="stretch",
    )

    if not provider.is_available():
        st.info(provider.message)

    # TODO: map desk labels to Bloomberg tickers/ISINs to pull live ref data.
    # TODO(workspace): enrich definitions from Workspace historical later.
