"""
components.py — shared look and building blocks: the minimal black/white/red
styling, the full-screen countdown hero, and section headers.
"""
import html as html_lib

import streamlit as st
import streamlit.components.v1 as components

import config
from config import BLACK, FONT, GREY, PANEL, PANEL_EDGE, RED, RULE, WHITE


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
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], footer,
        [data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"],
        [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none; }}
        .block-container {{ padding: 4.5rem 1.5rem 6rem; max-width: 980px; }}

        /* top tabs */
        header[data-testid="stHeader"] {{ background: {BLACK}; border-bottom: 1px solid {RULE}; }}
        header [data-testid="stTopNavLink"], header a {{ border-radius: 0 !important; }}
        header [data-testid="stTopNavLink"] span, header a span {{
            font-size: .68rem !important; letter-spacing: .16em; text-transform: uppercase; color: {GREY};
        }}
        header [data-testid="stTopNavLink"]:hover span {{ color: {WHITE}; }}
        header [aria-current="page"] {{ background: transparent !important; }}
        header [aria-current="page"] span {{ color: {RED} !important; }}
        hr {{ border-color: {RULE} !important; margin: 2rem 0 !important; }}

        [data-testid="stMetricLabel"] p {{
            text-transform: uppercase; letter-spacing: .14em; font-size: .65rem; color: {GREY};
        }}
        [data-testid="stMetricValue"] {{ font-size: 1.8rem; font-weight: 400; letter-spacing: -.02em; }}
        [data-testid="stExpander"] details {{ border: none; border-top: 1px solid {RULE}; border-radius: 0; }}
        [data-testid="stExpander"] summary p {{ font-size: .75rem; letter-spacing: .12em;
            text-transform: uppercase; color: {GREY}; }}

        .sw-section {{ margin: 2rem 0 2.5rem; display: flex; justify-content: space-between;
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
        /* panels: barely-lighter boxes that keep sections apart */
        [class*="st-key-panel-"] {{
            background: {PANEL}; border: 1px solid {PANEL_EDGE} !important; border-radius: 10px;
            padding: 1.8rem 2rem 2rem !important; margin-bottom: 1.4rem;
        }}
        [class*="st-key-panel-"] .sw-steps, [class*="st-key-panel-"] .sw-stats {{
            border: none; margin-top: 0; margin-bottom: 0;
        }}
        [class*="st-key-panel-"] .sw-step:first-child, [class*="st-key-panel-"] .sw-stat:first-child {{ padding-left: 0; }}
        @media (max-width: 640px) {{ [class*="st-key-panel-"] {{ padding: 1.2rem 1.1rem 1.4rem !important; }} }}

        /* every slider: room for the floating value above the handle */
        [data-testid="stSlider"] {{ padding-top: 1.8rem; }}

        /* section nav arrow */
        .sw-nav {{ display: flex; flex-direction: column; align-items: center; gap: 10px; margin: 5rem 0 1rem; }}
        .sw-nav a {{ width: 52px; height: 52px; border: 1px solid {RULE}; border-radius: 50%;
            display: flex; align-items: center; justify-content: center; font-size: 20px;
            color: {WHITE} !important; text-decoration: none; transition: border-color .2s, color .2s; }}
        .sw-nav a:hover {{ border-color: {RED}; color: {RED} !important; }}
        .sw-nav span {{ font-size: .62rem; letter-spacing: .22em; color: {GREY}; text-transform: uppercase; }}

        /* explainer steps */
        .sw-steps {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0;
            border-top: 1px solid {RULE}; border-bottom: 1px solid {RULE}; margin-bottom: 2.5rem; }}
        .sw-step {{ padding: 1.4rem 1.4rem 1.6rem 0; }}
        .sw-step + .sw-step {{ padding-left: 1.4rem; border-left: 1px solid {RULE}; }}
        .sw-step .i {{ color: {RED}; font-size: .7rem; letter-spacing: .14em; }}
        .sw-step .h {{ color: {WHITE}; font-size: .9rem; margin: .6rem 0 .5rem; }}
        .sw-step .b {{ color: {GREY}; font-size: .74rem; line-height: 1.65; }}
        .sw-step .b b {{ color: {WHITE}; font-weight: 400; }}

        /* live formulas */
        .sw-formula {{ padding: 1rem 0; border-bottom: 1px solid {RULE}; }}
        .sw-formula .l {{ font-size: .62rem; letter-spacing: .18em; color: {GREY}; margin-bottom: .6rem; }}
        .sw-formula .eq {{ display: flex; flex-wrap: wrap; align-items: flex-start; gap: 4px 12px; }}
        .sw-formula .t {{ display: flex; flex-direction: column; }}
        .sw-formula .v {{ color: {WHITE}; font-size: 1.05rem; }}
        .sw-formula .v.r {{ color: {RED}; }}
        .sw-formula .c {{ color: {GREY}; font-size: .58rem; letter-spacing: .1em; margin-top: 3px;
            text-transform: uppercase; }}
        .sw-formula .op {{ color: {GREY}; font-size: 1.05rem; }}

        /* assumption cards */
        .sw-a {{ font-size: .8rem; color: {WHITE}; margin-top: 1.4rem; }}
        .sw-a .k {{ color: {RED}; font-size: .65rem; letter-spacing: .12em; margin-right: 6px; }}
        .sw-a .x {{ color: {GREY}; font-size: .7rem; line-height: 1.6; margin-top: .3rem; }}

        /* case-study page */
        .sw-lede {{ color: {WHITE}; font-size: .95rem; line-height: 1.75; max-width: 720px; }}
        .sw-lede b {{ color: {RED}; font-weight: 400; }}
        .sw-stats {{ display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 2.5rem;
            border-top: 1px solid {RULE}; border-bottom: 1px solid {RULE}; }}
        .sw-stat {{ padding: 1.3rem 1rem 1.4rem 0; }}
        .sw-stat + .sw-stat {{ padding-left: 1rem; border-left: 1px solid {RULE}; }}
        .sw-stat .v {{ font-size: 1.7rem; color: {WHITE}; letter-spacing: -.02em; }}
        .sw-stat .v.r {{ color: {RED}; }}
        .sw-stat .c {{ font-size: .62rem; color: {GREY}; letter-spacing: .08em; margin-top: .5rem;
            text-transform: uppercase; line-height: 1.5; }}
        .sw-tl {{ margin-top: 1.2rem; border-left: 1px solid {RULE}; }}
        .sw-tl .e {{ display: grid; grid-template-columns: 120px 1fr; gap: 18px; padding: .9rem 0 .9rem 1.4rem;
            position: relative; }}
        .sw-tl .e::before {{ content: ''; position: absolute; left: -4px; top: 1.25rem; width: 7px; height: 7px;
            border-radius: 50%; background: {GREY}; }}
        .sw-tl .e.hot::before {{ background: {RED}; }}
        .sw-tl .d {{ color: {GREY}; font-size: .72rem; padding-top: 2px; }}
        .sw-tl .e.hot .d {{ color: {RED}; }}
        .sw-tl .h {{ color: {WHITE}; font-size: .88rem; }}
        .sw-tl .b {{ color: {GREY}; font-size: .74rem; line-height: 1.6; margin-top: .25rem; }}
        .sw-takeaway {{ color: {WHITE}; font-size: .9rem; line-height: 1.7; margin: 1.4rem 0 .4rem; }}
        .sw-takeaway b {{ color: {RED}; font-weight: 400; }}

        @media (max-width: 640px) {{
            .sw-day {{ grid-template-columns: 1fr; }}
            .sw-steps, .sw-stats {{ grid-template-columns: 1fr 1fr; }}
            .sw-tl .e {{ grid-template-columns: 1fr; gap: 4px; }}
            .sw-step + .sw-step {{ padding-left: 0; border-left: none; border-top: 1px solid {RULE}; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def panel(name):
    """A softly lit box that separates one block of content from the next.
    Use as:  with panel("chart"): ...   (name must be unique on the page)"""
    return st.container(border=True, key=f"panel-{name}")


def section(number, title, meta="", anchor=""):
    st.markdown(
        f'<div id="{anchor}" class="sw-section"><div><span class="n">{number}</span>&nbsp;&nbsp;'
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
      .down {{ position:absolute; bottom:36px; background:none; border:1px solid {RULE}; color:{WHITE};
               width:52px; height:52px; border-radius:50%; font-size:20px; cursor:pointer;
               font-family:{FONT}; animation:b 2.4s ease-in-out infinite; transition:border-color .2s; }}
      .down:hover {{ border-color:{RED}; color:{RED}; }}
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
      <button class="down" id="down" title="Latest news">↓</button>
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
      // Fill exactly one screen, whatever the visitor's window size
      // Height = window height minus where the hero starts on the page, so the
      // next section always starts just below the fold. Re-checked on resize
      // (fullscreen on/off) and periodically, because Streamlit can reset it.
      function fit() {{
        const f = window.frameElement;
        if (!f) return;
        const main = window.parent.document.querySelector('section.stMain');
        const top = f.getBoundingClientRect().top + (main ? main.scrollTop : 0);
        const h = Math.max(420, window.parent.innerHeight - top) + 'px';
        if (f.style.height !== h) {{ f.style.height = h; f.setAttribute('height', parseInt(h)); }}
        // Streamlit's wrapper keeps the original 760px; resize it too so the
        // news section starts below the fold instead of overlapping
        const wrap = f.closest('[data-testid="stElementContainer"]');
        if (wrap && wrap.style.height !== h) {{ wrap.style.height = h; wrap.style.minHeight = h; }}
      }}
      fit(); window.parent.addEventListener('resize', fit); setInterval(fit, 400);
      // The hero lives in an iframe, so navigate the parent page to the News tab
      // (the frame can't change the page address itself, so it clicks the News tab)
      function go() {{
        const doc = window.parent.document;
        const link = [...doc.querySelectorAll('header a')].find(a => (a.getAttribute('href') || '').endsWith('news'));
        if (link) link.click();
      }}
      document.getElementById('down').addEventListener('click', go);
    </script>
    """
    components.html(page, height=760)


def nav_arrow(target, label, symbol="↓"):
    """Round arrow button linking to another tab (by its url_path)."""
    st.markdown(
        f'<div class="sw-nav"><a href="{target}" target="_self">{symbol}</a><span>{label}</span></div>',
        unsafe_allow_html=True,
    )


def explainer():
    """Three-step plain-English story of forced selling."""
    steps = [
        ("Index funds copy a list",
         "Trillions of dollars sit in passive funds that hold exactly what's in MSCI's Emerging Markets "
         "index. They don't pick stocks. They mirror the list."),
        ("The list changes",
         "If MSCI moves Indonesia to Standalone, Indonesian stocks drop off that list. Every fund copying it "
         "must sell its Indonesian shares, whatever the price or the company's quality."),
        ("The market can only absorb so much",
         "Only so much stock changes hands each day. Sell too fast and the price collapses, so funds spread "
         "it out. The days this takes is the <b>days of forced selling</b>, a measure of how long the "
         "pressure lasts."),
    ]
    cells = "".join(
        f'<div class="sw-step"><div class="i">{i:02d}</div><div class="h">{h}</div><div class="b">{b}</div></div>'
        for i, (h, b) in enumerate(steps, 1)
    )
    st.markdown(f'<div class="sw-steps">{cells}</div>', unsafe_allow_html=True)


def formula(label, parts, result):
    """One line like:  IF DOWNGRADED  $500bn × 1.5% × 100% × 1.0 = $7.50bn
    parts = [(value, caption), ...] so each number is labelled underneath."""
    terms = '<span class="op">×</span>'.join(
        f'<span class="t"><span class="v">{v}</span><span class="c">{c}</span></span>' for v, c in parts)
    st.markdown(
        f'<div class="sw-formula"><div class="l">{label}</div><div class="eq">{terms}'
        f'<span class="op">=</span><span class="t"><span class="v r">{result}</span><span class="c">&nbsp;</span>'
        f'</span></div></div>',
        unsafe_allow_html=True,
    )


def assumption(code, title, text):
    st.markdown(
        f'<div class="sw-a"><span class="k">{code}</span> {title}<div class="x">{text}</div></div>',
        unsafe_allow_html=True,
    )


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
