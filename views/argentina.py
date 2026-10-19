"""Argentina tab: case study of the last country MSCI moved to Standalone."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
import data
import model
from components import panel, fmt_usd, formula, nav_arrow, section
from config import BLACK, FONT, GREY, RED, RULE, WHITE

AR_DAY0 = "2021-06-24"       # MSCI announces Argentina -> Standalone
AR_EFFECTIVE = "2021-11-30"  # change takes effect at the November 2021 review

# --- data -------------------------------------------------------------------
with st.spinner("Loading Argentina market history…"):
    ar = data.load_many(("^MERV", "ARS=X", "ARGT", "YPF", "GGAL"), start="2020-06-01")  # one request
    merv, ars, argt, ypf, ggal = (ar[t] for t in ("^MERV", "ARS=X", "ARGT", "YPF", "GGAL"))
    jci = data.load_prices(config.INDEX_TICKER, start="2026-06-01")

# Merval is quoted in pesos; with ~50% inflation that hides the real loss.
# Convert to dollars at the official rate (which itself understates the fall).
merv_usd = (merv["Close"] / ars["Close"].reindex(merv.index).ffill()).dropna()


def move(close, start, end=None):
    """% change from the close on `start` to `end` (or the low after `start`)."""
    close = close.dropna()
    base = close.loc[:start].iloc[-1]
    later = close.loc[start:end] if end else close.loc[start:]
    return later.iloc[-1] / base * 100 - 100, later.min() / base * 100 - 100


argt_eff, _ = move(argt["Close"], AR_DAY0, AR_EFFECTIVE)
_, argt_low = move(argt["Close"], AR_DAY0, "2022-06-24")   # lowest point within a year
day1 = argt["Close"].loc[AR_DAY0:].iloc[1] / argt["Close"].loc[:AR_DAY0].iloc[-1] * 100 - 100

# ============================================================================
section("03", "Case study: Argentina, 2021", "THE LAST COUNTRY MSCI MADE STANDALONE")

with panel("intro"):
    st.markdown(
        """<p class="sw-lede">In June 2021, MSCI did to Argentina what it now proposes for Indonesia. It cut the
        country from Emerging Markets to <b>Standalone</b>, the lowest tier. The reason was capital controls that had
        stopped foreign investors from moving money freely since 2019. Five years later, Argentina is still there.</p>""",
        unsafe_allow_html=True)

    # --- big numbers ----------------------------------------------------------------
    stats = [
        (f"{day1:+.1f}%", "ARGT, the day after the announcement"),
        (f"{argt_eff:+.1f}%", "ARGT by the effective date (30 Nov 2021)"),
        (f"{argt_low:+.1f}%", "ARGT at its low, within a year"),
        ("5 yrs+", "still Standalone (2026 review)"),
    ]
    st.markdown(
        '<div class="sw-stats">' + "".join(
            f'<div class="sw-stat"><div class="v{" r" if v.startswith("-") else ""}">{v}</div><div class="c">{c}</div></div>'
            for v, c in stats) + "</div>",
        unsafe_allow_html=True)

with panel("timeline"):
    # --- timeline ---------------------------------------------------------------------
    st.markdown('<div class="sw-label" style="margin-bottom:.4rem">What happened</div>', unsafe_allow_html=True)
    events = [
        ("2009", "Downgraded to Frontier", "MSCI drops Argentina from Emerging Markets over capital controls.", False),
        ("Jun 2018", "Promoted back to EM", "Under market-friendly reforms, MSCI announces Argentina will rejoin EM.", False),
        ("Sep 2019", "Capital controls return", "After a currency crisis, the government reimposes the cepo (strict FX limits).", False),
        ("24 Jun 2021", "Standalone announced", "MSCI says the controls break its accessibility rules. ADRs fall, some by 11%+.", True),
        ("30 Nov 2021", "Change takes effect", "Argentina leaves MSCI EM. Funds tracking the index must have sold by this date.", True),
        ("2022 – 2026", "Still Standalone", "Annual reviews keep Argentina in the lowest tier. Upgrade talk returns, but no move.", False),
    ]
    st.markdown(
        '<div class="sw-tl">' + "".join(
            f'<div class="e{" hot" if hot else ""}"><div class="d">{d}</div><div><div class="h">{h}</div>'
            f'<div class="b">{b}</div></div></div>'
            for d, h, b, hot in events) + "</div>",
        unsafe_allow_html=True)

with panel("chart"):
    # --- the chart: event study ----------------------------------------------------
    st.markdown('<div class="sw-label" style="margin-bottom:.6rem">How the market moved, before vs after the announcement</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<p class="sw-note" style="font-size:.74rem !important">Two different years on one clock. Each line counts '
        'trading days from <b style="color:#F5F5F5;font-weight:400">its own country\'s announcement</b> '
        '(Argentina: 24 Jun 2021 · Indonesia: 15 Oct 2026), and every line is rescaled so that day equals 100. '
        'Left of 0 is the run-up; right of 0 is what happened after. Below 100 means lower than on announcement day.</p>',
        unsafe_allow_html=True)
    lo, hi = st.slider("Show days before ↔ after the announcement", -60, 250, (-30, 120))

    series = {
        "Argentina ETF (ARGT) · day 0 = 24 Jun 2021": (data.event_window(argt["Close"], AR_DAY0, 60, 250), WHITE, 1.6, None),
        "Merval in USD · 2021": (data.event_window(merv_usd, AR_DAY0, 60, 250), GREY, 1.1, None),
        "YPF (ADR) · 2021": (data.event_window(ypf["Close"], AR_DAY0, 60, 250), GREY, 1.1, "dot"),
        "Indonesia JCI · day 0 = 15 Oct 2026": (data.event_window(jci["Close"], config.ANNOUNCEMENT_DATE, 60, 250), RED, 2.2, None),
    }
    eff_day = len(argt["Close"].loc[AR_DAY0:AR_EFFECTIVE]) - 1  # trading days from announcement to effective

    fig = go.Figure()
    for name, (s, color, width, dash) in series.items():
        s = s[(s.index >= lo) & (s.index <= hi)]
        fig.add_trace(go.Scatter(x=s.index, y=s.values, name=name, mode="lines",
                                 line=dict(color=color, width=width, dash=dash),
                                 hovertemplate=f"{name}<br>day %{{x}}: %{{y:.1f}}<extra></extra>"))
    fig.add_hline(y=100, line=dict(color=RULE, width=1))
    fig.add_vline(x=0, line=dict(color=GREY, width=1, dash="dot"))
    # shade the run-up and label both sides so "before" vs "after" reads at a glance
    if lo < 0:
        fig.add_vrect(x0=lo, x1=0, fillcolor="rgba(255,255,255,0.025)", line_width=0, layer="below")
        fig.add_annotation(x=0, y=0, yref="paper", text="← BEFORE ANNOUNCEMENT  ", showarrow=False,
                           font=dict(color=GREY, size=9), xanchor="right", yanchor="bottom")
    fig.add_annotation(x=0, y=0, yref="paper", text="  AFTER ANNOUNCEMENT →", showarrow=False,
                       font=dict(color=GREY, size=9), xanchor="left", yanchor="bottom")
    if lo <= eff_day <= hi:
        fig.add_vline(x=eff_day, line=dict(color=GREY, width=1, dash="dot"))
        fig.add_annotation(x=eff_day, y=1, yref="paper", text="EFFECTIVE", showarrow=False,
                           font=dict(color=GREY, size=9), xanchor="left", yanchor="top")
    fig.add_annotation(x=0, y=1, yref="paper", text="DAY 0 · ANNOUNCED", showarrow=False,
                       font=dict(color=GREY, size=9), xanchor="left", yanchor="top")
    fig.update_layout(
        height=420, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=GREY, size=10), hovermode="x unified",
        legend=dict(orientation="h", y=-0.22, x=0, font=dict(size=10)),
        xaxis=dict(showgrid=False, linecolor=RULE, zeroline=False, range=[lo, hi],
                   title=dict(text="trading days from each country's announcement", font=dict(size=10, color=GREY))),
        yaxis=dict(showgrid=False, side="right", zeroline=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # one-line comparison at the same point in time
    jci_s, argt_s = series["Indonesia JCI · day 0 = 15 Oct 2026"][0], series["Argentina ETF (ARGT) · day 0 = 24 Jun 2021"][0]
    if not jci_s.empty and jci_s.index.max() > 0:
        n = jci_s.index.max()
        gap = jci_s.loc[n] - argt_s.loc[n]
        st.markdown(
            f'<p class="sw-takeaway">{n} trading day{"s" if n != 1 else ""} after its announcement, the JCI is '
            f'<b>{abs(gap):.1f} points {"below" if gap < 0 else "above"}</b> where Argentina was at the same point.</p>',
            unsafe_allow_html=True)
    st.markdown(
        '<p class="sw-note">ARGT is a US-listed ETF of Argentine companies (it includes MercadoLibre), so it shows the hit '
        'in dollars. The Merval is converted at the official peso rate, which understates the true currency loss. '
        'The red line only runs to today, because Indonesia\'s story is still unfolding and we never use future data '
        'for it. ARGT\'s later lows also reflect Argentina\'s inflation and November 2021 elections, not only MSCI.</p>',
        unsafe_allow_html=True)

with panel("force"):
    # --- forced selling -------------------------------------------------------------
    st.markdown('<div class="sw-label" style="margin-bottom:.4rem">How much was force-sold?</div>', unsafe_allow_html=True)
    st.markdown(
        """<p class="sw-lede" style="font-size:.85rem">No one published an official figure. Argentina was tiny in the index,
        about <b>0.1–0.3%</b> of MSCI EM, because only a few US-listed companies qualified. Running it through the
        same model as the simulator:</p>""", unsafe_allow_html=True)
    ar_out = model.country_outflow(500e9, 0.2, 100, 1.0)
    id_out = model.country_outflow(500e9, config.DEFAULTS["indonesia_weight"], 100, 1.0)
    formula("ARGENTINA 2021: our estimate", [
        ("$500bn", "passive money*"), ("0.2%", "Argentina share"), ("100%", "that sell"), ("1", "standalone"),
    ], fmt_usd(ar_out))
    formula("INDONESIA NOW: same model", [
        ("$500bn", "passive money*"), (f'{config.DEFAULTS["indonesia_weight"]:.1f}%', "Indonesia share"),
        ("100%", "that sell"), ("1", "standalone"),
    ], fmt_usd(id_out))
    st.markdown(
        f'<p class="sw-takeaway">Indonesia\'s forced selling would be roughly <b>{id_out / ar_out:.0f}× larger</b> '
        f'than Argentina\'s.</p>'
        '<p class="sw-note">* Illustrative estimate, not a reported figure. The same rough assumptions as the simulator '
        'are used for both, so the comparison matters more than either number.</p>',
        unsafe_allow_html=True)

with panel("lessons"):
    # --- lessons --------------------------------------------------------------------
    st.markdown('<div class="sw-label" style="margin-bottom:.4rem">What it means for Indonesia</div>', unsafe_allow_html=True)
    lessons = [
        ("The first hit was small",
         "ARGT fell only about 2% the next day, then even rallied. The real damage built over the following months, as the "
         "downgrade combined with inflation and politics."),
        ("Standalone is sticky",
         "Argentina has been stuck there since 2021. Getting back in means convincing MSCI over several annual reviews."),
        ("Size changes everything",
         "Argentina was a rounding error in EM. Indonesia is roughly 1.5% of it, so the same rule moves far more money."),
    ]
    st.markdown(
        '<div class="sw-steps">' + "".join(
            f'<div class="sw-step"><div class="i">{i:02d}</div><div class="h">{h}</div><div class="b">{b}</div></div>'
            for i, (h, b) in enumerate(lessons, 1)) + "</div>",
        unsafe_allow_html=True)

st.markdown(
    '<p class="sw-note">Sources: MSCI 2021 Market Classification Review (announced 24 Jun 2021, effective Nov 2021 review); '
    'Bloomberg, Infobae and El Economista coverage of the market reaction; Schroders on Argentina\'s EM weight; '
    'prices from Yahoo Finance.</p>', unsafe_allow_html=True)

nav_arrow("./", "Back to the countdown", "↑")  # the default tab lives at the site root