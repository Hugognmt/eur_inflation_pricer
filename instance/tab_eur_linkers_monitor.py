"""Tab: EUR_Linkers — monitor board for EUR inflation-linked govies."""

import pandas as pd
import streamlit as st

from instance import config


def render(provider) -> None:
    st.subheader("EUR_Linkers")
    st.caption("Linker monitor board.")

    st.dataframe(
        pd.DataFrame(config.linker_bonds()),
        hide_index=True,
        width="stretch",
    )

    st.info(
        "Live prices/yields need the desk labels mapped to Bloomberg tickers "
        "(coming next). Bloomberg available: %s." % provider.is_available()
    )

    # TODO(workspace): switch to Workspace live for real-time refresh later.
