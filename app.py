"""
app.py — Standalone Watch.
One scrolling page: countdown → news feed → outflow simulator.
Run with:  streamlit run app.py
"""
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
import data
import model
import news
from components import apply_style, fmt_pct, fmt_usd, hero, news_feed, section
from config import BLACK, FONT, GREY, RED, RULE, WHITE

st.set_page_config(page_title="Standalone Watch", page_icon="▼", layout="centered",
                   initial_sidebar_state="collapsed")
apply_style()


@st.cache_data(ttl=60 * 60, show_spinner=False)
def load_news():
    """Refresh headlines at most once an hour; fall back to the saved CSV."""
    try:
        df = news.update()
    except Exception:
        df = news.load_saved()
    return df, datetime.now(config.WIB)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
fx = data.load_prices(config.FX_TICKER)
jci = data.load_prices(config.INDEX_TICKER)
prices = {t[0]: data.load_prices(t[0]) for t in config.UNIVERSE}

# ===========================================================================
# 1. HERO — the countdown, alone on screen
# ===========================================================================
hero(data.change_since(jci), None if fx.empty else fx["Close"].iloc[-1])

# ===========================================================================
# 2. NEWS FEED
# ===========================================================================
stories, fetched_at = load_news()
section("01", "The downgrade, day by day",
        f"UPDATED {fetched_at:%d %b %H:%M} WIB · {len(stories)} STORIES")

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

# ===========================================================================
# 3. SIMULATOR
# ===========================================================================
section("02", "Forced-selling simulator", "ILLUSTRATIVE ESTIMATES — NOT INVESTMENT ADVICE")

scenario = st.segmented_control("Scenario", list(config.SCENARIOS), default="Standalone",
                                label_visibility="collapsed") or "Standalone"

D = config.DEFAULTS
with st.expander("Assumptions"):
    a, b = st.columns(2, gap="large")
    probability = a.slider("Probability of downgrade (%)", 0, 100, D["probability"])
    pct_sell = a.slider("% of passive holders that sell", 0, 100, D["pct_sell"])
    days_to_exit = a.slider("Days to exit", 1, 120, D["days_to_exit"])
    passive_aum_bn = b.number_input("Passive AUM tracking MSCI EM ($bn)", 0, 5000, D["passive_aum_bn"], step=50)
    indonesia_weight = b.number_input("Indonesia weight in MSCI EM (%)", 0.0, 10.0, D["indonesia_weight"], step=0.1)
    participation = b.slider("Participation rate (% of daily volume)", 1, 50, D["participation"])

# --- model ---------------------------------------------------------------
weights = data.free_float_weights(config.UNIVERSE, prices, config.UNIVERSE_COVERAGE)
c_out = model.country_outflow(passive_aum_bn * 1e9, indonesia_weight, pct_sell, config.SCENARIOS[scenario])

rows = []
for ticker, name, sector, fintech in config.UNIVERSE:
    info = data.load_info(ticker)
    w = weights[ticker]
    out = model.stock_outflow(c_out, w) if w else None
    adv = data.avg_daily_traded_value_usd(prices[ticker], fx)
    days = model.days_of_forced_selling(out, adv, participation) if out is not None else None
    pb = info["priceToBook"]
    rows.append({
        "_ticker": ticker, "Ticker": ticker.replace(".JK", ""), "Name": name, "Fintech": fintech,
        "Weight": w, "Outflow": out, "ADV": adv, "Days": days,
        "Since": data.change_since(prices[ticker]), "P/E": info["trailingPE"] or float("nan"), "P/B": pb or float("nan"),
    })
table = pd.DataFrame(rows)
table[["Days", "P/E", "P/B"]] = table[["Days", "P/E", "P/B"]].apply(pd.to_numeric, errors="coerce")
# Relative flag: heavier forced selling AND cheaper than the median name
table["Oversold"] = (table["Days"] > table["Days"].median()) & (table["P/B"] < table["P/B"].median())

# --- headline numbers ---------------------------------------------------
m1, m2, m3 = st.columns(3)
m1.metric("Expected outflow", fmt_usd(model.expected_value(c_out, probability)))
m2.metric("If downgraded", fmt_usd(c_out))
m3.metric("Probability", f"{probability}%")

# --- forced seller vs fundamentals ---------------------------------------
st.write("")
st.markdown('<div class="sw-label">Forced selling vs fundamentals</div>', unsafe_allow_html=True)
show = table.sort_values("Days", ascending=False).copy()
show["Ticker"] = show.apply(lambda r: r["Ticker"] + (" ◆" if r["Fintech"] else ""), axis=1)
show["Flag"] = show["Oversold"].map({True: "OVERSOLD?", False: ""})
show[["Outflow", "ADV"]] = show[["Outflow", "ADV"]] / 1e6
st.dataframe(
    show[["Ticker", "Weight", "Outflow", "ADV", "Days", "P/B", "P/E", "Since", "Flag"]],
    hide_index=True, use_container_width=True,
    column_config={
        "Weight": st.column_config.NumberColumn("Wt", format="percent"),
        "Outflow": st.column_config.NumberColumn("Out $m", format="%.0f"),
        "ADV": st.column_config.NumberColumn("ADV $m", format="%.1f"),
        "Days": st.column_config.NumberColumn("Days", format="%.1f"),
        "P/B": st.column_config.NumberColumn(format="%.1f"),
        "P/E": st.column_config.NumberColumn(format="%.1f"),
        "Since": st.column_config.NumberColumn("Δ 15 Oct", format="%+.1f%%"),
        "Flag": st.column_config.TextColumn(""),
    },
)
st.markdown(
    f'<p class="sw-note">◆ fintech &nbsp;·&nbsp; Days = outflow ÷ (20-day avg traded value × participation) '
    f'&nbsp;·&nbsp; OVERSOLD? = more forced selling and lower P/B than the median name. '
    f'The selling is driven by index rules, not valuation.</p>',
    unsafe_allow_html=True)

# --- single stock --------------------------------------------------------
st.write("")
labels = {r["_ticker"]: f'{r["Ticker"]}  {r["Name"]}' for r in rows}
pick = st.selectbox("Stock", list(labels), format_func=labels.get, label_visibility="collapsed")
row = table.set_index("_ticker").loc[pick]

s1, s2, s3 = st.columns(3)
s1.metric("Outflow", fmt_usd(row["Outflow"]))
s2.metric("Days of forced selling", "—" if pd.isna(row["Days"]) else f'{row["Days"]:.1f}')
s3.metric("Since 15 Oct", fmt_pct(row["Since"]))

df = prices[pick]
if not df.empty:
    after = df.index >= config.ANNOUNCEMENT_DATE
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", line=dict(color=WHITE, width=1.2),
                             hovertemplate="%{x|%d %b}  IDR %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df.index[after], y=df["Close"][after], mode="lines+markers",
                             line=dict(color=RED, width=1.6), marker=dict(size=4),
                             hovertemplate="%{x|%d %b}  IDR %{y:,.0f}<extra></extra>"))
    fig.update_layout(
        height=260, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor=BLACK, paper_bgcolor=BLACK,
        font=dict(family=FONT, color=GREY, size=10), showlegend=False,
        xaxis=dict(showgrid=False, linecolor=RULE), yaxis=dict(showgrid=False, side="right"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with st.expander("Methodology & assumptions"):
    st.markdown(f"""
- **Country outflow** = passive AUM × Indonesia weight × % that sell × scenario factor
  (Stay EM 0 · Frontier {config.SCENARIOS['Frontier']} · Standalone 1). The Frontier factor is an assumption.
- **Index weights**: free-float market cap (shares × (1 − insider holding %) × latest price, from yfinance), as a share of our
  9 stocks, × an assumed {config.UNIVERSE_COVERAGE:.0%} coverage of MSCI Indonesia. These are not official MSCI weights.
  The EIDO holdings file would be better, but iShares blocks free download.
- **ADV** = 20-day average of close × volume, converted at the latest USD/IDR. Post-crash volumes are unusually high,
  so ADV may overstate normal liquidity.
- **Days of forced selling** = stock outflow ÷ (ADV × participation rate). **Expected** = outflow × probability.
- **P/E, P/B** from yfinance (may lag). GoTo is loss-making, so it has no P/E.
- Prices are from Yahoo Finance and may be delayed. The decision date ({config.DECISION_DATE:%d %b %Y}) is expected,
  because MSCI has only said "by end of June 2027".
""")
