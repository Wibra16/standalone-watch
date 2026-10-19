"""Simulator tab: forced-selling model for Indonesia."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
import data
import model
from components import (panel, assumption, explainer, fmt_pct, fmt_usd, formula, nav_arrow, section)
from config import BLACK, FONT, GREY, RED, RULE, WHITE

with st.spinner("Loading prices for 23 stocks…"):
    fx = data.load_prices(config.FX_TICKER)
    prices = {t[0]: data.load_prices(t[0]) for t in config.UNIVERSE}
    for t in config.UNIVERSE:
        data.load_info(t[0])  # warm the fundamentals cache

section("02", "Forced-selling simulator", "ILLUSTRATIVE ESTIMATES — NOT INVESTMENT ADVICE")
with panel("explainer"):
    explainer()

# Plain-English meaning of each table column (hover tooltips + the explainer list)
GLOSSARY = {
    "Ticker": "The stock's code on the Indonesia Stock Exchange (BBCA = Bank Central Asia). "
              "◆ marks the fintech and digital-finance names.",
    "Wt": "Weight: the stock's estimated share of the MSCI Indonesia index. Bigger weight means index funds hold "
          "more of it, so they must sell more.",
    "Out $m": "Outflow: dollars of this stock that index funds would be forced to sell, in millions.",
    "ADV $m": "Average daily value: how many dollars of this stock change hands on a normal day (20-day average), "
              "in millions. It measures how easy the stock is to sell.",
    "Days": "Days of forced selling: how many trading days it takes to sell the outflow without crashing the "
            "price, if sellers stay under the participation rate. Higher means a longer squeeze.",
    "P/B": "Price-to-book: share price ÷ the company's net assets per share. Below 1 means the market values the "
           "company at less than its accounts say it's worth, which is cheap.",
    "P/E": "Price-to-earnings: share price ÷ yearly profit per share. Lower means cheaper. Blank means the "
           "company is losing money.",
    "Δ 15 Oct": "How much the share price has moved since MSCI's proposal on 15 Oct 2026.",
    "Flag": "OVERSOLD? = more forced selling and a lower P/B than the typical stock here. These may be falling "
            "because of index rules rather than the business itself. Not in index = trades too little "
            "(under $100k a day) for MSCI funds to hold.",
}

SCENARIO_NOTES = {
    "Stay EM": "MSCI backs down. Indonesia stays in the index, so nobody is forced to sell.",
    "Frontier": "Moved to the Frontier index. EM funds sell, but some Frontier funds buy, so about 85% of the selling remains.",
    "Standalone": "Dropped from both indexes. Every fund tracking MSCI EM must sell its Indonesian shares.",
}
with panel("scenario"):
    st.markdown('<div class="sw-label">What MSCI decides</div>', unsafe_allow_html=True)
    scenario = st.segmented_control("Scenario", list(config.SCENARIOS), default="Standalone",
                                    label_visibility="collapsed") or "Standalone"
    st.markdown(f'<p class="sw-note">{SCENARIO_NOTES[scenario]}</p>', unsafe_allow_html=True)

    # Results are drawn here, above the sliders, but filled in after the sliders run.
    results = st.container()

    # --- assumptions: each one a slider plus a plain-English line ----------------
    D = config.DEFAULTS
    st.write("")
    with st.container(key="assume"), st.expander("Change the assumptions · drag the sliders and watch the numbers move"):
        a, b = st.columns(2, gap="large")
        with a:
            assumption("A1", "Passive money tracking MSCI EM",
                       "Dollars in index funds that copy MSCI Emerging Markets, in billions (500 = $500bn). Rough industry estimate.")
            passive_aum_bn = st.number_input("$ billions", 0, 20000, D["passive_aum_bn"], step=50,
                                             help="In billions of US dollars. 1,000 = $1 trillion.")
            assumption("A2", "Indonesia's share of the index",
                       "Of every $100 in an EM fund, about this much is in Indonesian stocks.")
            indonesia_weight = st.number_input("%", 0.0, 10.0, D["indonesia_weight"], step=0.1, label_visibility="collapsed")
            assumption("A3", "Share of funds that actually sell",
                       "100% means every tracker exits. Lower it if some funds keep holdings or have flexible mandates.")
            pct_sell = st.slider("pct_sell", 0, 100, D["pct_sell"], format="%d%%", label_visibility="collapsed")
        with b:
            assumption("A4", "Probability MSCI goes through with it",
                       "Your estimate. It turns the 'if downgraded' outflow into an expected outflow.")
            probability = st.slider("prob", 0, 100, D["probability"], format="%d%%", label_visibility="collapsed")
            assumption("A5", "Participation rate",
                       "The share of a stock's normal daily trading that sellers can be without crashing the price. "
                       "Traders often use 10–25%.")
            participation = st.slider("part", 1, 50, D["participation"], format="%d%%", label_visibility="collapsed")
            assumption("A6", "Days funds take to exit",
                       "If funds squeeze the selling into this many days, how big is it compared with normal trading?")
            days_to_exit = st.slider("days", 1, 120, D["days_to_exit"], format="%d days", label_visibility="collapsed")

# --- model ---------------------------------------------------------------
usd_idr = fx["Close"].iloc[-1] if not fx.empty else None
adv_all = {t[0]: data.avg_daily_traded_value_usd(prices[t[0]], fx) for t in config.UNIVERSE}
eligible = {t for t, adv in adv_all.items() if adv and adv >= config.MIN_ADV_USD}
weights = data.free_float_weights(config.UNIVERSE, prices, config.UNIVERSE_COVERAGE, eligible)
factor = config.SCENARIOS[scenario]
c_out = model.country_outflow(passive_aum_bn * 1e9, indonesia_weight, pct_sell, factor)
expected = model.expected_value(c_out, probability)

rows = []
for ticker, name, sector, fintech in config.UNIVERSE:
    info = data.load_info(ticker)
    w = weights[ticker]
    out = model.stock_outflow(c_out, w) if w else None
    adv = adv_all[ticker]
    days = model.days_of_forced_selling(out, adv, participation) if out else None
    pe, pb = (data.valuation(info, prices[ticker]["Close"].iloc[-1], usd_idr)
              if usd_idr and not prices[ticker].empty else (None, None))
    rows.append({
        "_ticker": ticker, "Ticker": ticker.replace(".JK", ""), "Name": name, "Fintech": fintech,
        "Weight": w, "Outflow": out, "ADV": adv, "Days": days,
        "Pressure": model.daily_pressure_pct_of_adv(out, adv, days_to_exit) if out is not None else None,
        "Since": data.change_since(prices[ticker]), "P/E": pe, "P/B": pb,
        "Status": "" if ticker in eligible else "Not in index",
    })
table = pd.DataFrame(rows)
num = ["Days", "P/E", "P/B", "Pressure"]
table[num] = table[num].apply(pd.to_numeric, errors="coerce")
# Relative flag: heavier forced selling AND cheaper than the median name
table["Oversold"] = (table["Days"] > table["Days"].median()) & (table["P/B"] < table["P/B"].median())

# --- headline numbers + how they're calculated (drawn above the sliders) ----
with results:
    st.write("")
    m1, m2 = st.columns(2)
    m1.metric("If downgraded", fmt_usd(c_out))
    m2.metric("Expected outflow", fmt_usd(expected))
    formula("IF DOWNGRADED: total Indonesian stock passive funds must sell", [
        (f"${passive_aum_bn:,}bn", "A1 passive money"),
        (f"{indonesia_weight:.1f}%", "A2 Indonesia share"),
        (f"{pct_sell}%", "A3 that sell"),
        (f"{factor:g}", f"{scenario} factor"),
    ], fmt_usd(c_out))
    formula("EXPECTED OUTFLOW: the same amount, weighted by how likely it is", [
        (fmt_usd(c_out), "if downgraded"),
        (f"{probability}%", "A4 probability"),
    ], fmt_usd(expected))
    st.write("")

with panel("table"):
    # --- forced seller vs fundamentals ---------------------------------------
    st.write("")
    st.markdown('<div class="sw-label">Forced selling vs fundamentals</div>', unsafe_allow_html=True)
    show = table.sort_values("Days", ascending=False).copy()
    show["Ticker"] = show.apply(lambda r: r["Ticker"] + (" ◆" if r["Fintech"] else ""), axis=1)
    show["Flag"] = show["Oversold"].map({True: "OVERSOLD?", False: ""})
    show.loc[show["Status"] != "", "Flag"] = show["Status"]
    show[["Outflow", "ADV"]] = show[["Outflow", "ADV"]] / 1e6
    st.dataframe(
        show[["Ticker", "Weight", "Outflow", "ADV", "Days", "P/B", "P/E", "Since", "Flag"]],
        hide_index=True, use_container_width=True, height=(len(show) + 1) * 35 + 3,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", help=GLOSSARY["Ticker"]),
            "Weight": st.column_config.NumberColumn("Wt", format="percent", help=GLOSSARY["Wt"]),
            "Outflow": st.column_config.NumberColumn("Out $m", format="%.0f", help=GLOSSARY["Out $m"]),
            "ADV": st.column_config.NumberColumn("ADV $m", format="%.1f", help=GLOSSARY["ADV $m"]),
            "Days": st.column_config.NumberColumn("Days", format="%.1f", help=GLOSSARY["Days"]),
            "P/B": st.column_config.NumberColumn(format="%.1f", help=GLOSSARY["P/B"]),
            "P/E": st.column_config.NumberColumn(format="%.1f", help=GLOSSARY["P/E"]),
            "Since": st.column_config.NumberColumn("Δ 15 Oct", format="%+.1f%%", help=GLOSSARY["Δ 15 Oct"]),
            "Flag": st.column_config.TextColumn("", help=GLOSSARY["Flag"]),
        },
    )
    st.markdown('<p class="sw-note">Hover over a column name for a quick explanation, or open the list below.</p>',
                unsafe_allow_html=True)
    with st.expander("What do these columns mean?"):
        st.markdown(
            '<div class="sw-gloss">' + "".join(
                f'<div class="g"><div class="n">{name}</div><div class="d">{text}</div></div>'
                for name, text in GLOSSARY.items()) + "</div>",
            unsafe_allow_html=True)

with panel("stock"):
    # --- single stock --------------------------------------------------------
    st.write("")
    labels = {r["_ticker"]: f'{r["Ticker"]}  {r["Name"]}' for r in rows}
    pick = st.selectbox("Stock", list(labels), format_func=labels.get, label_visibility="collapsed")
    row = table.set_index("_ticker").loc[pick]

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Must be sold", fmt_usd(row["Outflow"]))
    s2.metric("Days of forced selling", "—" if pd.isna(row["Days"]) else f'{row["Days"]:,.0f}')
    s3.metric(f"× normal volume", "—" if pd.isna(row["Pressure"]) else f'{row["Pressure"] / 100:,.1f}×',
              help=f"Selling it all in {days_to_exit} days (A6), compared with a normal day's trading")
    s4.metric("Since 15 Oct", fmt_pct(row["Since"]))
    if not pd.isna(row["Days"]):
        st.markdown(
            f'<p class="sw-note">Funds would need to sell {fmt_usd(row["Outflow"])} of {row["Ticker"]}. '
            f'About {fmt_usd(row["ADV"])} of it trades on a normal day, and sellers can be {participation}% of that, '
            f'so the exit takes about <b style="color:#F5F5F5;font-weight:400">{row["Days"]:,.0f} trading days</b>.</p>',
            unsafe_allow_html=True)

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
            height=260, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family=FONT, color=GREY, size=10), showlegend=False,
            xaxis=dict(showgrid=False, linecolor=RULE), yaxis=dict(showgrid=False, side="right"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with st.expander("Methodology & assumptions"):
    st.markdown(f"""
- **Country outflow** = passive AUM × Indonesia weight × % that sell × scenario factor
  (Stay EM 0 · Frontier {config.SCENARIOS['Frontier']} · Standalone 1). The Frontier factor is an assumption.
- **Index weights**: free-float market cap (shares × (1 − insider holding %) × latest price, from yfinance), as a share of our
  stocks, × an assumed {config.UNIVERSE_COVERAGE:.0%} coverage of MSCI Indonesia. These are not official MSCI weights.
  The EIDO holdings file would be better, but iShares blocks free download.
- **Liquidity screen**: stocks trading under ${config.MIN_ADV_USD:,.0f}/day are treated as outside the MSCI index
  (weight 0), since MSCI screens out very illiquid names. This currently drops thinly traded names like DCII and CASA.
- **ADV** = 20-day average of close × volume, converted at the latest USD/IDR. Post-crash volumes are unusually high,
  so ADV may overstate normal liquidity.
- **Days of forced selling** = stock outflow ÷ (ADV × participation rate). **Expected** = outflow × probability.
- **P/E, P/B** = latest price ÷ EPS or book value per share from yfinance. For companies that report in USD, book value is converted to rupiah first. Loss-makers (e.g. GoTo) have no P/E.
- Prices are from Yahoo Finance and may be delayed. The decision date ({config.DECISION_DATE:%d %b %Y}) is expected,
  because MSCI has only said "by end of June 2027".
""")

nav_arrow("argentina", "What happened to Argentina")