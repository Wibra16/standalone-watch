"""
app.py — Standalone Watch.
Four tabs along the top: Home (countdown) · News · Simulator · Argentina.
Run with:  streamlit run app.py
"""
import streamlit as st

from components import apply_style

st.set_page_config(page_title="Standalone Watch", page_icon="▼", layout="centered",
                   initial_sidebar_state="collapsed")
apply_style()

nav = st.navigation(
    [
        st.Page("views/home.py", title="Home", default=True),
        st.Page("views/updates.py", title="News", url_path="news"),
        st.Page("views/simulator.py", title="Simulator", url_path="simulator"),
        st.Page("views/argentina.py", title="Argentina 2021", url_path="argentina"),
    ],
    position="top",
)
nav.run()
