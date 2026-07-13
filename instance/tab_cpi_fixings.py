"""Tab: CPI / Fixings — latest CPI/HICP levels and a short history."""

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
    st.subheader("CPI_Matrix")
    st.caption("EUR area / France CPI reference indices.")

    tickers = config.CPI_TICKERS

    if not provider.is_available():
        st.warning(provider.message)
        st.dataframe(pd.DataFrame({"ticker": tickers}), width="stretch")
        return

    # Latest level snapshot.
    snap = provider.get_snapshot(tickers, ["PX_LAST", "SECURITY_NAME"])
    if snap.empty:
        st.info("No snapshot returned from Bloomberg. Showing configured tickers.")
        snap = pd.DataFrame({"ticker": tickers})
    st.dataframe(snap, width="stretch")

    # Short history line chart.
    end = dt.date.today()
    start = end - dt.timedelta(days=config.DEFAULT_LOOKBACK_DAYS)
    hist = provider.get_history(tickers, "PX_LAST", start, end)
    if not hist.empty:
        _line_chart(hist, "CPI history")
        st.download_button(
            "Download CPI history (CSV)",
            hist.to_csv().encode("utf-8"),
            file_name="cpi_history.csv",
            mime="text/csv",
        )
    else:
        st.caption("No history available for the selected window.")

    # TODO(workspace): add published-vs-forecast fixings from Workspace later.
