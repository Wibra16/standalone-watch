"""About tab: what the site is, who made it, and the legal notices."""
import streamlit as st

from components import about_block, panel, section

section("04", "About", "IDXDOWN")

with panel("what"):
    st.markdown(
        """<p class="sw-lede">IDXDown follows MSCI's proposal to move Indonesia from Emerging Markets to
        <b>Standalone</b> status. It counts down to the decision, tracks the news day by day, estimates how much
        stock index funds would be forced to sell, and compares it all with Argentina, the last country MSCI
        made Standalone.</p>""", unsafe_allow_html=True)

with panel("legal"):
    about_block()
