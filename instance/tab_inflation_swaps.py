"""Tab: Inflation Swaps — EUR zero-coupon inflation swap levels and history."""

import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st

from instance import config


def _line_chart(hist: pd.DataFrame, title: str):
    """Plot a bdh history frame (possibly MultiIndex columns) with Plotly."""
    df = hist.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(c) for c in col).strip() for col in df.columns]
    df = df.reset_index()
    date_col = df.columns[0]
    long = df.melt(id_vars=date_col, var_name="series", value_name="value")
    fig = px.line(long, x=date_col, y="value", color="series", title=title)
    st.plotly_chart(fig, use_container_width=True)


def render(provider) -> None:
    st.subheader("INF_Swaps")
    st.caption("EUR zero-coupon inflation swaps (HICPxT).")

    tickers = config.INFLATION_SWAP_TICKERS

    if not provider.is_available():
        st.warning(provider.message)
        st.dataframe(pd.DataFrame({"ticker": tickers}), width="stretch")
        return

    # Latest swap levels.
    snap = provider.get_snapshot(tickers, ["PX_LAST"])
    if snap.empty:
        st.info("No snapshot returned from Bloomberg. Showing configured tickers.")
        snap = pd.DataFrame({"ticker": tickers})
    st.dataframe(snap, width="stretch")

    # Short history line chart (simple term-structure through time).
    end = dt.date.today()
    start = end - dt.timedelta(days=config.DEFAULT_LOOKBACK_DAYS)
    hist = provider.get_history(tickers, "PX_LAST", start, end)
    if not hist.empty:
        _line_chart(hist, "Inflation swaps history")
    else:
        st.caption("No history available for the selected window.")

    # TODO(workspace): overlay Workspace live quotes for intraday moves later.
