"""Tab: EUR_Bonds — monitor board for EUR nominal govies."""

import pandas as pd
import streamlit as st

from instance import config


def render(provider) -> None:
    st.subheader("EUR_Bonds")
    st.caption("Nominal monitor board.")

    st.dataframe(
        pd.DataFrame(config.nominal_bonds()),
        hide_index=True,
        width="stretch",
    )

    st.info(
        "Live prices/yields need the desk labels mapped to Bloomberg tickers "
        "(coming next). Bloomberg available: %s." % provider.is_available()
    )

    # TODO(workspace): switch to Workspace live for real-time refresh later.
