"""
components.py — shared look and building blocks: the minimal black/white/red
styling, the full-screen countdown hero, and section headers.
"""
import html as html_lib

import streamlit as st
import streamlit.components.v1 as components

import config
from config import BLACK, FONT, GREY, RED, RULE, WHITE


def apply_style():
    """Minimal terminal styling. SF Mono is built into macOS; other systems
    fall back to their own monospace font."""
    st.markdown(
        f"""
        <style>
        /* SF Mono everywhere except Streamlit's icon font */
        .stApp *:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded) {{
            font-family: {FONT} !important;
        }}
        .stApp {{ background: {BLACK}; color: {WHITE}; }}
        header[data-testid="stHeader"], [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"], footer {{ display: none; }}
        .block-container {{ padding: 0 1.5rem 6rem; max-width: 980px; }}
        hr {{ border-color: {RULE} !important; margin: 2rem 0 !important; }}

        [data-testid="stMetricLabel"] p {{
            text-transform: uppercase; letter-spacing: .14em; font-size: .65rem; color: {GREY};
        }}
        [data-testid="stMetricValue"] {{ font-size: 1.8rem; font-weight: 400; letter-spacing: -.02em; }}
        [data-testid="stExpander"] details {{ border: none; border-top: 1px solid {RULE}; border-radius: 0; }}
        [data-testid="stExpander"] summary p {{ font-size: .75rem; letter-spacing: .12em;
            text-transform: uppercase; color: {GREY}; }}

        .sw-section {{ margin: 7rem 0 2.5rem; display: flex; justify-content: space-between;
            align-items: baseline; border-bottom: 1px solid {RULE}; padding-bottom: .8rem; }}
        .sw-section .n {{ color: {RED}; font-size: .72rem; letter-spacing: .16em; }}
        .sw-section .t {{ font-size: 1.05rem; letter-spacing: .02em; color: {WHITE}; }}
        .sw-section .m {{ color: {GREY}; font-size: .68rem; letter-spacing: .1em; }}
        .sw-label {{ text-transform: uppercase; letter-spacing: .14em; font-size: .65rem; color: {GREY}; }}
        .sw-note, .stMarkdown p.sw-note {{ color: {GREY}; font-size: .7rem !important; line-height: 1.6; }}

        /* news feed */
        .sw-day {{ display: grid; grid-template-columns: 92px 1fr; gap: 0 24px;
            padding: 1.1rem 0; border-bottom: 1px solid {RULE}; }}
        .sw-day .d {{ color: {GREY}; font-size: .72rem; letter-spacing: .08em; padding-top: 3px; }}
        .sw-item {{ margin-bottom: .85rem; line-height: 1.45; }}
        .sw-item:last-child {{ margin-bottom: 0; }}
        .sw-item a {{ color: {WHITE} !important; text-decoration: none; font-size: .86rem; }}
        .sw-item a:hover {{ color: {RED} !important; }}
        .sw-item .s {{ color: {GREY}; font-size: .68rem; margin-top: 2px; }}
        .sw-item .s b {{ color: {RED}; font-weight: 400; }}
        @media (max-width: 640px) {{ .sw-day {{ grid-template-columns: 1fr; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section(number, title, meta=""):
    st.markdown(
        f'<div class="sw-section"><div><span class="n">{number}</span>&nbsp;&nbsp;'
        f'<span class="t">{title}</span></div><span class="m">{meta}</span></div>',
        unsafe_allow_html=True,
    )


def hero(jci_change, fx_last):
    """Full-screen opening: just the countdown. Rendered as HTML/JS so it
    ticks every second without re-running Python."""
    decision_ms = int(config.DECISION_DATE.timestamp() * 1000)
    close_ms = int(config.CONSULTATION_CLOSE.timestamp() * 1000)
    status = "confirmed" if config.DECISION_CONFIRMED else "expected"
    jci = "—" if jci_change is None else f"{jci_change:+.1f}%"
    fx = "—" if fx_last is None else f"{fx_last:,.0f}"

    page = f"""
    <style>
      * {{ margin:0; box-sizing:border-box; }}
      body {{ background:{BLACK}; color:{WHITE}; font-family:{FONT}; }}
      .wrap {{ height:100vh; display:flex; flex-direction:column; justify-content:center;
               align-items:center; text-align:center; position:relative; }}
      .lbl {{ font-size:11px; letter-spacing:.24em; color:{GREY}; text-transform:uppercase; }}
      .clock {{ display:flex; gap:clamp(14px,4vw,44px); margin:28px 0 30px; }}
      .u {{ display:flex; flex-direction:column; align-items:center; }}
      .v {{ font-size:clamp(44px,11vw,120px); font-weight:300; letter-spacing:-.04em; line-height:1;
            font-variant-numeric:tabular-nums; }}
      .k {{ font-size:10px; letter-spacing:.24em; color:{GREY}; margin-top:12px; }}
      .red {{ color:{RED}; }}
      .sub {{ font-size:12px; color:{GREY}; letter-spacing:.06em; line-height:2; }}
      .sub span {{ color:{WHITE}; }}
      .down {{ position:absolute; bottom:28px; font-size:10px; letter-spacing:.24em; color:{GREY};
               animation:b 2.4s ease-in-out infinite; }}
      @keyframes b {{ 50% {{ transform:translateY(6px); opacity:.5; }} }}
    </style>
    <div class="wrap">
      <div class="lbl">MSCI decision on Indonesia &nbsp;·&nbsp; <span class="red">{status}</span>
        {config.DECISION_DATE:%d %b %Y}</div>
      <div class="clock">
        <div class="u"><div class="v" id="d">—</div><div class="k">DAYS</div></div>
        <div class="u"><div class="v" id="h">—</div><div class="k">HRS</div></div>
        <div class="u"><div class="v" id="m">—</div><div class="k">MIN</div></div>
        <div class="u"><div class="v red" id="s">—</div><div class="k">SEC</div></div>
      </div>
      <div class="sub">
        Consultation closes in <span id="c">—</span> days<br>
        JCI <span class="red">{jci}</span> &nbsp;·&nbsp; USD/IDR <span>{fx}</span> &nbsp; since proposal
      </div>
      <div class="down">SCROLL ↓</div>
    </div>
    <script>
      const p = n => String(n).padStart(2, '0');
      function tick() {{
        const ms = Math.max(0, {decision_ms} - Date.now());
        document.getElementById('d').textContent = Math.floor(ms / 864e5);
        document.getElementById('h').textContent = p(Math.floor(ms % 864e5 / 36e5));
        document.getElementById('m').textContent = p(Math.floor(ms % 36e5 / 6e4));
        document.getElementById('s').textContent = p(Math.floor(ms % 6e4 / 1e3));
        document.getElementById('c').textContent = Math.max(0, Math.ceil(({close_ms} - Date.now()) / 864e5));
      }}
      tick(); setInterval(tick, 1000);
    </script>
    """
    components.html(page, height=760)


def news_feed(df, limit_days, skip_days=0, per_day=None):
    """Day-by-day list, newest first. Only headline/source/link are shown."""
    if df.empty:
        st.markdown('<p class="sw-note">No stories loaded. Google News may be unreachable.</p>',
                    unsafe_allow_html=True)
        return
    df = df.copy()
    df["day"] = df["published"].dt.tz_convert(config.WIB).dt.date
    blocks = []
    for day, items in list(df.groupby("day", sort=False))[skip_days:skip_days + limit_days]:
        rows = []
        for _, r in items.head(per_day).iterrows():
            tags = " · ".join(f"<b>{t}</b>" for t in str(r["tags"]).split(",") if t)
            lang = " · ID" if r["language"] == "id" else ""
            rows.append(
                f'<div class="sw-item"><a href="{html_lib.escape(r["link"])}" target="_blank">'
                f'{html_lib.escape(r["headline"])}</a>'
                f'<div class="s">{html_lib.escape(str(r["source"]))}{lang} &nbsp; {tags}</div></div>'
            )
        blocks.append(f'<div class="sw-day"><div class="d">{day:%d %b}<br>{day:%a}</div>'
                      f'<div>{"".join(rows)}</div></div>')
    st.markdown("".join(blocks), unsafe_allow_html=True)


def fmt_usd(x):
    if x is None or x != x:  # None or NaN
        return "—"
    if abs(x) >= 1e9:
        return f"${x / 1e9:,.2f}bn"
    return f"${x / 1e6:,.0f}m"


def fmt_pct(x):
    return "—" if x is None else f"{x:+.1f}%"
