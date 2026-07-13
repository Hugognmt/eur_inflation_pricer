import streamlit as st

try:
    import blpapi  # Bloomberg API (bbg)
    from xbbg import blp
    BBG_AVAILABLE = True
except ImportError:
    BBG_AVAILABLE = False

st.set_page_config(page_title="Test", page_icon="🧪")
st.title("Test")

if not BBG_AVAILABLE:
    st.error(
        "Bloomberg (bbg) libraries not available. "
        "Install `blpapi` and `xbbg`, and ensure a Bloomberg Terminal is running."
    )
    st.stop()

st.success("Bloomberg (bbg) libraries imported successfully.")

ticker = st.text_input("Ticker", value="EURUSD Curncy")
field = st.text_input("Field", value="PX_LAST")

if st.button("Fetch"):
    data = blp.bdp(tickers=ticker, flds=field)
    st.dataframe(data)
