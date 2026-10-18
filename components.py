"""
components.py — pieces shared by every page: the terminal-style CSS,
the disclaimer, and the live countdown banner.
"""
import streamlit as st
import streamlit.components.v1 as components

import config
from config import BLACK, GREY, RED, WHITE


def apply_style():
    """Minimal black/white/red 'trading terminal' styling."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&display=swap');
        html, body, [class*="css"], .stMarkdown, .stMetric, input, label, button {{
            font-family: 'IBM Plex Mono', monospace !important;
        }}
        .stApp {{ background: {BLACK}; }}
        header[data-testid="stHeader"] {{ background: transparent; }}
        section[data-testid="stSidebar"] {{ background: {BLACK}; border-right: 1px solid #1E1E1E; }}
        .block-container {{ padding-top: 1.5rem; max-width: 1200px; }}
        hr {{ border-color: #1E1E1E !important; margin: 1.2rem 0 !important; }}
        h1, h2, h3 {{ letter-spacing: -0.02em; font-weight: 700; }}

        /* metrics: small uppercase label, big number */
        [data-testid="stMetricLabel"] p {{
            text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.68rem; color: {GREY};
        }}
        [data-testid="stMetricValue"] {{ font-size: 1.9rem; font-weight: 500; }}

        .sw-label {{ text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.7rem; color: {GREY}; }}
        .sw-disclaimer {{
            border: 1px solid {RED}; color: {RED}; padding: 6px 12px; font-size: 0.72rem;
            letter-spacing: 0.12em; text-transform: uppercase; display: inline-block;
        }}
        .sw-tape {{ white-space: nowrap; overflow: hidden; border-top: 1px solid #1E1E1E;
            border-bottom: 1px solid #1E1E1E; padding: 6px 0; font-size: 0.8rem; color: {WHITE}; }}
        .sw-dn {{ color: {RED}; }}
        .sw-up {{ color: {WHITE}; }}
        .sw-tag {{ border: 1px solid {RED}; color: {RED}; font-size: 0.62rem; padding: 1px 6px;
            letter-spacing: 0.1em; margin-left: 6px; vertical-align: middle; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def disclaimer():
    st.markdown(
        '<span class="sw-disclaimer">Illustrative estimates — not investment advice</span>',
        unsafe_allow_html=True,
    )


def countdown_banner():
    """Live countdown, rendered in a tiny HTML/JS block so it ticks every
    second without re-running the Python app."""
    decision_ms = int(config.DECISION_DATE.timestamp() * 1000)
    close_ms = int(config.CONSULTATION_CLOSE.timestamp() * 1000)
    status = "CONFIRMED" if config.DECISION_CONFIRMED else "EXPECTED"
    decision_label = config.DECISION_DATE.strftime("%d %b %Y").upper()
    close_label = config.CONSULTATION_CLOSE.strftime("%d %b %Y").upper()

    html = f"""
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <div style="font-family:'IBM Plex Mono',monospace;color:{WHITE};background:{BLACK};
                display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:16px;
                border-bottom:1px solid #1E1E1E;padding-bottom:14px;">
      <div>
        <div style="font-size:11px;letter-spacing:.16em;color:{GREY};">
          MSCI DECISION · INDONESIA → STANDALONE ·
          <span style="color:{RED};">{status}</span> {decision_label}
        </div>
        <div id="main" style="font-size:52px;font-weight:700;letter-spacing:-.02em;line-height:1.1;margin-top:4px;"></div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:11px;letter-spacing:.16em;color:{GREY};">CONSULTATION CLOSES {close_label}</div>
        <div id="sub" style="font-size:22px;font-weight:500;margin-top:4px;"></div>
      </div>
    </div>
    <script>
      function fmt(ms, big) {{
        if (ms <= 0) return '<span style="color:{RED}">00D 00H 00M</span>';
        const d = Math.floor(ms / 864e5), h = Math.floor(ms % 864e5 / 36e5),
              m = Math.floor(ms % 36e5 / 6e4), s = Math.floor(ms % 6e4 / 1e3);
        const p = n => String(n).padStart(2, '0');
        const sec = big ? ` <span style="color:{RED}">${{p(s)}}S</span>` : '';
        return `${{d}}D ${{p(h)}}H ${{p(m)}}M` + sec;
      }}
      function tick() {{
        const now = Date.now();
        document.getElementById('main').innerHTML = fmt({decision_ms} - now, true);
        document.getElementById('sub').innerHTML = fmt({close_ms} - now, false);
      }}
      tick(); setInterval(tick, 1000);
    </script>
    """
    components.html(html, height=140)


def fmt_usd(x):
    """$1.23bn / $456m style formatting."""
    if x is None:
        return "—"
    if abs(x) >= 1e9:
        return f"${x / 1e9:,.2f}bn"
    return f"${x / 1e6:,.0f}m"


def fmt_pct(x):
    return "—" if x is None else f"{x:+.1f}%"
