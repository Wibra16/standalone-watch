"""Home tab: the full-screen countdown, with the top 40 stocks scrolling at the sides."""
import streamlit as st

import config
import data
from components import hero

# This tab uses the full window width so the ticker columns sit at the screen edges
st.markdown("<style>.block-container { max-width: 100% !important; padding-left: 0 !important;"
            " padding-right: 0 !important; }</style>", unsafe_allow_html=True)

fx = data.load_prices(config.FX_TICKER)
jci = data.load_prices(config.INDEX_TICKER)
tape = data.last_closes(tuple(config.TOP75))
hero(data.change_since(jci), None if fx.empty else fx["Close"].iloc[-1], tape,
     None if jci.empty else f"{jci.index[-1]:%d %b %Y}")
