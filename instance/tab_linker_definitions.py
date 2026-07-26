"""Tab: BondDef_Infla — EUR inflation-linked bond definitions."""

import streamlit as st

from instance import bql_bonds, config


def render(provider) -> None:
    st.subheader("BondDef_Infla")
    st.caption("EUR inflation-linked bond names, retrieved from Bloomberg via BQL.")

    blocks = bql_bonds.run_blocks(provider, bql_bonds.LINKER_BLOCKS)
    df, source = bql_bonds.combine(blocks, config.linker_bonds)

    st.dataframe(df, hide_index=True, width="stretch")

    if source.startswith("Bloomberg"):
        st.success(f"Linker names loaded from {source} — {len(df)} bonds.")
    else:
        st.info(
            f"Showing static config ({len(df)} bonds); "
            f"{provider.message} BQL will repopulate names when connected."
        )

    _render_queries(blocks)

    # TODO(workspace): enrich definitions from Workspace historical later.


def _render_queries(blocks) -> None:
    """Show each BQL query used and its raw, unmodified output beneath it."""
    with st.expander("BQL queries used + raw output", expanded=False):
        for b in blocks:
            st.markdown(f"**{b['key']}**")
            st.code(b["query"], language="text")
            st.caption("Raw BQL output")
            if b["df"].empty:
                st.text("(no rows — Bloomberg unavailable or empty universe)")
            else:
                st.dataframe(b["df"], hide_index=True, width="stretch")
