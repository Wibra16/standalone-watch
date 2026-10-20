"""
export_site_data.py — build the JSON files the static website reads.

Runs the same data steps as the Streamlit app (prices, liquidity screen,
free-float weights, valuations, news, Argentina event study) and writes the
results to site/data/. The browser then does only the simple simulator math.

Run it any time (the daily GitHub Action runs it too):
    python export_site_data.py
"""
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("STREAMLIT_LOG_LEVEL", "error")  # data.py uses st.cache_data; quiet it

import pandas as pd

import config
import data
import news
from companies import PROFILES

OUT = Path(__file__).parent / "site" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def num(x, nd=4):
    """JSON-safe number: None for missing/NaN, rounded otherwise."""
    if x is None:
        return None
    try:
        if isinstance(x, float) and math.isnan(x):
            return None
        return round(float(x), nd)
    except (TypeError, ValueError):
        return None


def write(name, obj):
    path = OUT / name
    path.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False))
    print(f"  {name:16s} {path.stat().st_size / 1024:7.1f} KB")


# --- market + simulator inputs ------------------------------------------------
tickers = tuple(t[0] for t in config.UNIVERSE)
both = data.load_many((config.FX_TICKER, config.INDEX_TICKER))
fx, jci = both[config.FX_TICKER], both[config.INDEX_TICKER]
prices = data.load_many(tickers)
data.load_fundamentals(tickers)
usd_idr = fx["Close"].iloc[-1] if not fx.empty else None

adv_all = {t: data.avg_daily_traded_value_usd(prices[t], fx) for t in tickers}
eligible = {t for t, adv in adv_all.items() if adv and adv >= config.MIN_ADV_USD}
weights = data.free_float_weights(config.UNIVERSE, prices, config.UNIVERSE_COVERAGE, eligible)

stocks = []
for ticker, name, _sector, fintech in config.UNIVERSE:
    df = prices[ticker]
    info = data.load_info(ticker)
    pe, pb = (data.valuation(info, df["Close"].iloc[-1], usd_idr)
              if usd_idr and not df.empty else (None, None))
    bars = df.dropna(subset=["Open", "High", "Low", "Close"]) if not df.empty else pd.DataFrame(columns=["Open", "High", "Low", "Close"])
    closes = bars["Close"]
    stocks.append({
        "code": ticker.replace(".JK", ""),
        "name": name,
        "fintech": fintech,
        "weight": num(weights.get(ticker), 6),
        "adv": num(adv_all.get(ticker), 0),
        "eligible": ticker in eligible,
        "since": num(data.change_since(df), 2),
        "pe": num(pe, 2),
        "pb": num(pb, 2),
        "dates": [d.strftime("%Y-%m-%d") for d in closes.index],
        "close": [num(v, 2) for v in closes.values],
        "open": [num(v, 2) for v in bars["Open"].values],
        "high": [num(v, 2) for v in bars["High"].values],
        "low": [num(v, 2) for v in bars["Low"].values],
    })

tape = [{"code": c, "close": num(p, 2), "chg": num(ch, 2)} for c, p, ch in data.last_closes(tuple(config.TOP75))]

fx_chg = data.change_since(fx)
write("market.json", {
    "generated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
    "last_close": jci.index[-1].strftime("%Y-%m-%d") if not jci.empty else None,
    "jci_change": num(data.change_since(jci), 2),
    "fx_last": num(usd_idr, 0),
    "fx_change": num(fx_chg, 2),
    "tape": tape,
    "stocks": stocks,
})

# --- company cards ------------------------------------------------------------------
write("companies.json", {c: {"name": n, "about": a, "products": p} for c, (n, a, p) in PROFILES.items()})

# --- news ------------------------------------------------------------------------------
try:
    stories = news.update()
except Exception:
    stories = news.load_saved()
stories = stories.sort_values("published", ascending=False)
write("news.json", {
    "generated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
    "stories": [{
        "t": pd.Timestamp(r.published).tz_convert(config.WIB).strftime("%Y-%m-%d %H:%M"),
        "h": r.headline, "s": r.source, "l": r.link, "lang": r.language,
        "tags": [t for t in str(r.tags).split(",") if t and t != "nan"],
    } for r in stories.itertuples()],
})

# --- Argentina case study ----------------------------------------------------------------
AR_DAY0, AR_EFFECTIVE = "2021-06-24", "2021-11-30"
ar = data.load_many(("^MERV", "ARS=X", "ARGT", "YPF"), start="2020-06-01")
argt = ar["ARGT"]["Close"].dropna()
merv_usd = (ar["^MERV"]["Close"] / ar["ARS=X"]["Close"].reindex(ar["^MERV"].index).ffill()).dropna()
jci_long = data.load_prices(config.INDEX_TICKER, start="2026-06-01")["Close"].dropna()


def window(series, day0):
    w = data.event_window(series, day0, 60, 250)
    return {"x": [int(i) for i in w.index], "y": [num(v, 2) for v in w.values]}


def move(close, start, end):
    base = close.loc[:start].iloc[-1]
    later = close.loc[start:end]
    return later.iloc[-1] / base * 100 - 100, later.min() / base * 100 - 100


argt_eff, _ = move(argt, AR_DAY0, AR_EFFECTIVE)
_, argt_low = move(argt, AR_DAY0, "2022-06-24")
day1 = argt.loc[AR_DAY0:].iloc[1] / argt.loc[:AR_DAY0].iloc[-1] * 100 - 100
write("argentina.json", {
    "day1": num(day1, 2), "effective": num(argt_eff, 2), "low": num(argt_low, 2),
    "eff_day": int(len(argt.loc[AR_DAY0:AR_EFFECTIVE]) - 1),
    "series": {
        "argt": window(argt, AR_DAY0),
        "merv": window(merv_usd, AR_DAY0),
        "ypf": window(ar["YPF"]["Close"].dropna(), AR_DAY0),
        "jci": window(jci_long, config.ANNOUNCEMENT_DATE),
    },
})

# --- candlestick history: EIDO (how global investors see Indonesia) + JCI -------------
def ohlc(df):
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    return {"d": [d.strftime("%Y-%m-%d") for d in df.index],
            "o": [num(v, 3) for v in df["Open"]], "h": [num(v, 3) for v in df["High"]],
            "l": [num(v, 3) for v in df["Low"]], "c": [num(v, 3) for v in df["Close"]]}


hist = data.load_many(("EIDO", config.INDEX_TICKER), start="2025-04-01")
write("candles.json", {"eido": ohlc(hist["EIDO"]), "jci": ohlc(hist[config.INDEX_TICKER])})

# --- 4-hour candles (last ~60 days; Yahoo keeps hourly bars that long) -----------------
# Hourly bars are grouped into two sessions a day, in each market's own time:
# IDX 09:00 (morning, to the lunch break) and 13:00 (afternoon, to the close);
# EIDO in New York 09:30 and 13:30.
import yfinance as yf  # noqa: E402


def four_hour(df, tz, split, starts):
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if df.empty:
        return {"d": [], "o": [], "h": [], "l": [], "c": []}
    idx = df.index.tz_convert(tz)
    hours = idx.hour + idx.minute / 60
    keys = [f"{d:%Y-%m-%d} {starts[0] if h < split else starts[1]}" for d, h in zip(idx, hours)]
    g = df.assign(k=keys).groupby("k", sort=True)
    bars = pd.DataFrame({"o": g["Open"].first(), "h": g["High"].max(), "l": g["Low"].min(), "c": g["Close"].last()})
    return {"d": list(bars.index), **{k: [num(v, 3) for v in bars[k]] for k in "ohlc"}}


h4_tickers = [config.INDEX_TICKER, "EIDO"] + [t[0] for t in config.UNIVERSE]
try:
    raw = yf.download(h4_tickers, period="60d", interval="60m", progress=False, auto_adjust=False, group_by="ticker", threads=True)
    IDX = ("Asia/Jakarta", 13, ("09:00", "13:00"))
    write("intraday.json", {
        "jci": four_hour(raw[config.INDEX_TICKER], *IDX),
        "eido": four_hour(raw["EIDO"], "America/New_York", 13.5, ("09:30", "13:30")),
        "stocks": {t.replace(".JK", ""): four_hour(raw[t], *IDX) for t in h4_tickers[2:] if t in raw.columns.get_level_values(0)},
    })
except Exception as err:       # keep the previous file if Yahoo's hourly feed fails
    print("  intraday:", err)

# --- internet sentiment (Reddit) -------------------------------------------------------
import reddit  # noqa: E402

try:
    social = reddit.fetch()
except Exception as err:          # API down / key revoked: keep the site working
    print("  reddit:", err)
    social = None
write("social.json", {"generated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
                      "configured": social is not None, **(social or {"posts": []})})

# --- settings the page needs (dates, defaults, scenarios, author) --------------------------
write("config.json", {
    "announcement": config.ANNOUNCEMENT_DATE,
    "decision": config.DECISION_DATE.isoformat(),
    "decision_confirmed": config.DECISION_CONFIRMED,
    "consultation_close": config.CONSULTATION_CLOSE.isoformat(),
    "scenarios": config.SCENARIOS,
    "defaults": config.DEFAULTS,
    "coverage": config.UNIVERSE_COVERAGE,
    "min_adv": config.MIN_ADV_USD,
    "author": config.AUTHOR,
    "email": config.AUTHOR_EMAIL,
    "year": config.COPYRIGHT_YEAR,
})
print("Done →", OUT)
