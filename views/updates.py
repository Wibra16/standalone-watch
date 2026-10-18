"""News tab: the day-by-day feed."""
from datetime import datetime

import streamlit as st

import config
import news
from components import panel, nav_arrow, news_feed, section


@st.cache_data(ttl=60 * 60, show_spinner=False)
def load_news():
    """Refresh headlines at most once an hour; fall back to the saved CSV."""
    try:
        df = news.update()
    except Exception:
        df = news.load_saved()
    return df, datetime.now(config.WIB)


with st.spinner("Fetching the latest headlines…"):
    stories, fetched_at = load_news()
section("01", "The downgrade, day by day",
        f"UPDATED {fetched_at:%d %b %H:%M} WIB · {len(stories)} STORIES")

with panel("feed"):
    lang = st.segmented_control("Language", ["All", "English", "Bahasa"], default="All",
                                label_visibility="collapsed") or "All"
    shown = stories
    if lang != "All" and not stories.empty:
        shown = stories[stories["language"] == ("en" if lang == "English" else "id")]
    news_feed(shown, limit_days=3, per_day=4)
    with st.expander("More stories"):
        news_feed(shown, limit_days=60)
    st.markdown('<p class="sw-note">Headlines and links via Google News. Tags are keyword-based.</p>',
                unsafe_allow_html=True)
nav_arrow("simulator", "Simulate the sell-off")