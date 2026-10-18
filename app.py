"""
app.py — Standalone Watch, Phase 1: clickable outflow simulator.
Run with:  streamlit run app.py
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
import data
import model
from components import apply_style, countdown_banner, disclaimer, fmt_pct, fmt_usd
from config import BLACK, GREY, RED, WHITE

st.set_page_config(page_title="Standalone Watch", page_icon="▼", layout="wide")
apply_style()
countdown_banner()

# ---------------------------------------------------------------------------
# Sidebar: assumptions
# ---------------------------------------------------------------------------
D = config.DEFAULTS
with st.sidebar:
    st.markdown('<div class="sw-label">Assumptions</div>', unsafe_allow_html=True)
    probability = st.slider("Probability of downgrade (%)", 0, 100, D["probability"])
    passive_aum_bn = st.number_input("Passive AUM tracking MSCI EM ($bn)", 0, 5000, D["passive_aum_bn"], step=50)
    indonesia_weight = st.number_input("Indonesia weight in MSCI EM (%)", 0.0, 10.0, D["indonesia_weight"], step=0.1)
    pct_sell = st.slider("% of passive holders that sell", 0, 100, D["pct_sell"])
    days_to_exit = st.slider("Days to exit", 1, 120, D["days_to_exit"])
    participation = st.slider("Participation rate (% of daily volume)", 1, 50, D["participation"])
    st.caption("All defaults are rough illustrative estimates, not sourced figures.")

# ---------------------------------------------------------------------------
# Title + scenario toggle
# ---------------------------------------------------------------------------
left, right = st.columns([3, 2])
with left:
    st.markdown("# STANDALONE WATCH")
    st.markdown(
        f'<div class="sw-label">Simulating MSCI\'s proposed downgrade of Indonesia · '
        f'proposed {config.ANNOUNCEMENT_DATE}</div>',
        unsafe_allow_html=True,
    )
with right:
    st.write("")
    scenario = st.segmented_control(
        "Scenario", list(config.SCENARIOS), default="Standalone", label_visibility="collapsed"
    ) or "Standalone"
    disclaimer()

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
with st.spinner("Loading market data…"):
    fx = data.load_prices(config.FX_TICKER)
    jci = data.load_prices(config.INDEX_TICKER)
    prices = {t[0]: data.load_prices(t[0]) for t in config.UNIVERSE}

missing = [t for t, df in prices.items() if df.empty]
if missing:
    st.warning(f"No data from Yahoo Finance for: {', '.join(missing)}")

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
factor = config.SCENARIOS[scenario]
c_out = model.country_outflow(passive_aum_bn * 1e9, indonesia_weight, pct_sell, factor)

rows = []
for ticker, name, sector, fintech, weight in config.UNIVERSE:
    df = prices[ticker]
    out = model.stock_outflow(c_out, weight)
    adv = data.avg_daily_traded_value_usd(df, fx)
    rows.append({
        "Ticker": ticker.replace(".JK", ""),
        "_ticker": ticker,
        "Name": name,
        "Fintech": fintech,
        "Weight": weight,
        "Outflow": out,
        "Expected": model.expected_value(out, probability),
        "ADV": adv,
        "Days": model.days_of_forced_selling(out, adv, participation),
        "Pressure": model.daily_pressure_pct_of_adv(out, adv, days_to_exit),
        "Since": data.change_since(df),
    })
table = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# Ticker tape
# ---------------------------------------------------------------------------
tape = []
for r in rows:
    if r["Since"] is not None:
        cls = "sw-dn" if r["Since"] < 0 else "sw-up"
        arrow = "▼" if r["Since"] < 0 else "▲"
        tape.append(f'{r["Ticker"]} <span class="{cls}">{arrow} {abs(r["Since"]):.1f}%</span>')
st.markdown(f'<div class="sw-tape">{" &nbsp;·&nbsp; ".join(tape)} &nbsp;&nbsp;'
            f'<span style="color:{GREY}">SINCE {config.ANNOUNCEMENT_DATE}</span></div>',
            unsafe_allow_html=True)
st.write("")

# ---------------------------------------------------------------------------
# Headline metrics
# ---------------------------------------------------------------------------
fx_chg = data.change_since(fx)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Expected outflow", fmt_usd(model.expected_value(c_out, probability)),
          help="Country outflow × probability of downgrade")
m2.metric("Outflow if it happens", fmt_usd(c_out))
m3.metric("JCI since 15 Oct", fmt_pct(data.change_since(jci)))
m4.metric("IDR / USD", f"{fx['Close'].iloc[-1]:,.0f}" if not fx.empty else "—",
          f"{fx_chg:+.1f}% (weaker rupiah)" if fx_chg and fx_chg > 0 else fmt_pct(fx_chg),
          delta_color="inverse")

st.divider()

# ---------------------------------------------------------------------------
# Stock picker + chart
# ---------------------------------------------------------------------------
labels = {r["_ticker"]: f'{r["Ticker"]} · {r["Name"]}' + ("  [FINTECH]" if r["Fintech"] else "")
          for r in rows}
pick = st.selectbox("Stock", list(labels), format_func=labels.get)
row = table.set_index("_ticker").loc[pick]

tag = '<span class="sw-tag">FINTECH</span>' if row["Fintech"] else ""
st.markdown(f'### {row["Ticker"]} {tag}<div class="sw-label">{row["Name"]}</div>', unsafe_allow_html=True)

s1, s2, s3, s4 = st.columns(4)
s1.metric("Estimated outflow", fmt_usd(row["Outflow"]))
s2.metric("Days of forced selling", "—" if pd.isna(row["Days"]) else f'{row["Days"]:.1f}',
          help="Outflow ÷ (avg daily traded value × participation rate)")
s3.metric(f"Avg daily value ({config.ADV_WINDOW}d)", fmt_usd(row["ADV"]))
s4.metric("Price since 15 Oct", fmt_pct(row["Since"]))

df = prices[pick]
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines",
                             line=dict(color=WHITE, width=1.4), name=row["Ticker"],
                             hovertemplate="%{x|%d %b %Y}<br>IDR %{y:,.0f}<extra></extra>"))
    fig.add_vline(x=pd.Timestamp(config.ANNOUNCEMENT_DATE).value / 1e6,
                  line=dict(color=RED, width=1, dash="dot"))
    fig.add_annotation(x=config.ANNOUNCEMENT_DATE, y=1, yref="paper", text="MSCI PROPOSAL",
                       showarrow=False, font=dict(color=RED, size=10), xanchor="right", yanchor="top")
    fig.update_layout(
        height=340, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor=BLACK, paper_bgcolor=BLACK,
        font=dict(family="IBM Plex Mono, monospace", color=GREY, size=11), showlegend=False,
        xaxis=dict(showgrid=False, linecolor="#1E1E1E"),
        yaxis=dict(showgrid=True, gridcolor="#141414", zeroline=False, side="right"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# Full universe table
# ---------------------------------------------------------------------------
st.markdown('<div class="sw-label">Universe · ranked by days of forced selling</div>', unsafe_allow_html=True)
show = table.sort_values("Days", ascending=False)[
    ["Ticker", "Name", "Weight", "Outflow", "Expected", "ADV", "Days", "Pressure", "Since"]].copy()
show[["Outflow", "Expected", "ADV"]] = show[["Outflow", "Expected", "ADV"]] / 1e6  # show in $m
st.dataframe(
    show, hide_index=True, use_container_width=True,
    column_config={
        "Weight": st.column_config.NumberColumn("Index wt*", format="percent"),
        "Outflow": st.column_config.NumberColumn("Outflow $m", format="%.0f"),
        "Expected": st.column_config.NumberColumn("Expected $m", format="%.0f"),
        "ADV": st.column_config.NumberColumn("ADV $m", format="%.1f"),
        "Days": st.column_config.NumberColumn("Days forced", format="%.1f"),
        "Pressure": st.column_config.NumberColumn(f"% of ADV/day over {days_to_exit}d", format="%.0f%%"),
        "Since": st.column_config.NumberColumn("Since 15 Oct", format="%+.1f%%"),
    },
)
st.caption("* Index weights are illustrative guesses (Phase 1). ADV = average daily traded value, "
           "converted at the latest IDR/USD. Phase 2 replaces weights with free-float estimates.")

with st.expander("Assumptions & methodology"):
    st.markdown(f"""
- **Country outflow** = passive AUM × Indonesia weight × % that sell × scenario factor
  (Stay EM = 0, Frontier = {config.SCENARIOS['Frontier']}, Standalone = 1).
- **Per-stock outflow** = country outflow × stock's share of Indonesia's index weight (*illustrative in Phase 1*).
- **Days of forced selling** = per-stock outflow ÷ (20-day average daily traded value × participation rate).
- **Expected outflow** = outflow × probability of downgrade.
- Prices and volumes come from Yahoo Finance via yfinance, so they may be delayed or have gaps.
- The decision date ({config.DECISION_DATE:%d %b %Y}) is **expected**. MSCI has only said "by end of June 2027".
""")
